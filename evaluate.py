import os
import sys
import numpy as np
import pandas as pd
import math
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt

from eve import simulate_qkd_protocol, estimate_qber

def run_simulation(num_qubits, attack_strength, noise_level=0.0, attack_type="Standard Random", seed=None):
    sim_data = simulate_qkd_protocol(num_qubits, attack_strength, noise_level=noise_level, attack_type=attack_type, seed=seed)
    qber, raw_a, raw_b, adv_feat = estimate_qber(np.array(sim_data["alice_sifted"]), np.array(sim_data["bob_sifted"]), np.array(sim_data["sifted_bases"]), 0.25)
    return len(sim_data["alice_sifted"]), qber, 0, 0, 0, sim_data, adv_feat

def wilson_score_interval(successes, n, z=1.96):
    if n == 0: return 0, 0
    p = successes / n
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return center - spread, center + spread

def format_conf(successes, n):
    if n == 0: return "0.0%"
    p = successes / n
    low, high = wilson_score_interval(successes, n)
    return f"{p*100:.1f}% [{low*100:.1f}-{high*100:.1f}]"

def generate_data(num_sessions, qubits, base_seed=42):
    np.random.seed(base_seed)
    data = []
    
    scenarios = []
    # a) honest, noise 0-14% in steps of 1-2%
    for noise in [0, 2, 4, 6, 8, 10, 12, 14]:
        for _ in range(num_sessions):
            scenarios.append({'eve': 0, 'noise': noise/100.0, 'type': 'None', 'attack': False})
            
    # b) standard random intercept-resend at fractions 10, 20, 35, 50, 100%
    # c) basis-biased (Z-heavy) at the same fractions
    # d) combined with noise 0%, 3%, 6%
    for noise in [0, 3, 6]:
        for frac in [10, 20, 35, 50, 100]:
            for at in ["Standard Random", "Basis-Biased (Z-heavy)"]:
                for _ in range(num_sessions):
                    scenarios.append({'eve': frac/100.0, 'noise': noise/100.0, 'type': at, 'attack': True})
                    
    print(f"Generating {len(scenarios)} sessions...")
    np.random.shuffle(scenarios)
    
    for i, s in enumerate(scenarios):
        if i % 100 == 0:
            print(f"Running session {i}/{len(scenarios)}...")
        seed = base_seed + i
        s_len, qber, e_len, f_len, ss, sim_data, af = run_simulation(qubits, s['eve'], s['noise'], s['type'], seed=seed)
        
        s['seed'] = seed
        s['qber'] = qber
        s['qber_z'] = af['qber_z']
        s['qber_x'] = af['qber_x']
        s['qber_drift'] = af['qber_drift']
        s['max_burst'] = af['max_burst']
        s['sifted_ratio'] = s_len / qubits
        s['sifted_len'] = s_len
        s['seed'] = seed
        
        data.append(s)
        
    return pd.DataFrame(data)

def calc_metrics(df_sub, rule_col):
    y_true = df_sub['attack']
    y_pred = df_sub[rule_col]
    tp = ((y_true == True) & (y_pred == True)).sum()
    fp = ((y_true == False) & (y_pred == True)).sum()
    tn = ((y_true == False) & (y_pred == False)).sum()
    fn = ((y_true == True) & (y_pred == False)).sum()
    
    det_rate = format_conf(tp, tp+fn)
    fa_rate = format_conf(fp, fp+tn)
    acc = format_conf(tp+tn, tp+fp+tn+fn)
    
    prec = tp / (tp+fp) if (tp+fp)>0 else 0
    rec = tp / (tp+fn) if (tp+fn)>0 else 0
    f1 = 2 * prec * rec / (prec+rec) if (prec+rec)>0 else 0
    
    return {
        'Detection Rate': det_rate,
        'False Alarm Rate': fa_rate,
        'Accuracy': acc,
        'Precision': f"{prec:.3f}",
        'Recall': f"{rec:.3f}",
        'F1': f"{f1:.3f}"
    }

def main():
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    os.makedirs('results', exist_ok=True)
    dataset_path = 'results/eval_dataset.csv'
    
    if os.path.exists(dataset_path):
        print("Loading cached dataset...")
        df = pd.read_csv(dataset_path)
    else:
        df = generate_data(num_sessions=15, qubits=1000, base_seed=4242)
        df.to_csv(dataset_path, index=False)
        
    print(f"Total sessions: {len(df)}")
    features = ['qber', 'sifted_ratio', 'qber_z', 'qber_x', 'qber_drift', 'max_burst']
    
    # Train/Val/Test
    # Train on Standard Random + Noise(0, 4, 8, 12)
    # Test on Basis Biased + Noise(2, 6, 10, 14)
    # Plus the reverse!
    
    def evaluate_split(train_noise, train_type, test_noise, test_type, split_name):
        train_mask = df['noise'].isin(train_noise) & (df['type'].isin(['None', train_type]))
        test_mask = df['noise'].isin(test_noise) & (df['type'].isin(['None', test_type]))
        
        train_indices = df[train_mask].index.tolist()
        np.random.seed(1337)
        np.random.shuffle(train_indices)
        split_idx = int(0.8 * len(train_indices))
        train_idx = train_indices[:split_idx]
        val_idx = train_indices[split_idx:]
        test_idx = df[test_mask].index.tolist()
        
        X_train, y_train = df.loc[train_idx, features], df.loc[train_idx, 'attack']
        X_val, y_val = df.loc[val_idx, features], df.loc[val_idx, 'attack']
        X_test, y_test = df.loc[test_idx, features], df.loc[test_idx, 'attack']
        
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        best_p = 0.5; best_f1 = 0
        val_probs = model.predict_proba(X_val)[:, 1]
        for p_thresh in np.arange(0.1, 0.9, 0.05):
            preds = val_probs > p_thresh
            score = f1_score(y_val, preds) if sum(preds) > 0 else 0
            if score > best_f1:
                best_f1 = score
                best_p = p_thresh
                
        test_df = df.loc[test_idx].copy()
        test_df['ml_prob'] = model.predict_proba(X_test)[:, 1]
        test_df['RuleA_reject'] = test_df['qber'] > 0.11
        test_df['RuleB_reject'] = test_df['ml_prob'] > best_p
        test_df['RuleC_reject'] = test_df['RuleA_reject'] | test_df['RuleB_reject']
        
        summary = []
        for r_name, r_col in [('Rule A (Threshold)', 'RuleA_reject'), ('Rule B (ML)', 'RuleB_reject')]:
            metrics = calc_metrics(test_df, r_col)
            metrics['Rule'] = r_name
            metrics['Split'] = split_name
            summary.append(metrics)
            
        return test_df, pd.DataFrame(summary), best_p

    # Split 1: Train Standard, Test Biased
    test_df1, sum1, p1 = evaluate_split([0.0, 0.04, 0.08, 0.12], 'Standard Random', 
                                        [0.02, 0.06, 0.10, 0.14], 'Basis-Biased (Z-heavy)', 
                                        'Train Standard -> Test Biased')
                                        
    # Split 2: Train Biased, Test Standard
    test_df2, sum2, p2 = evaluate_split([0.0, 0.04, 0.08, 0.12], 'Basis-Biased (Z-heavy)', 
                                        [0.02, 0.06, 0.10, 0.14], 'Standard Random', 
                                        'Train Biased -> Test Standard')
                                        
    summary_df = pd.concat([sum1, sum2])
    summary_df.to_csv('results/summary.csv', index=False)
    
    # We will use Split 1's test_df for disagreements and plots to keep it simple, but let's label it.
    disagreements = test_df1[test_df1['RuleA_reject'] != test_df1['RuleB_reject']].copy()
    disagreements['RuleA'] = disagreements['RuleA_reject'].map({True: 'REJECTED', False: 'ACCEPTED'})
    disagreements['RuleB'] = disagreements['RuleB_reject'].map({True: 'REJECTED', False: 'ACCEPTED'})
    disagreements['CorrectVerdict'] = disagreements['attack'].map({True: 'REJECTED', False: 'ACCEPTED'})
    disagreements['WhoWasRight'] = np.where(disagreements['RuleA'] == disagreements['CorrectVerdict'], 'Rule A', 
                                   np.where(disagreements['RuleB'] == disagreements['CorrectVerdict'], 'Rule B (ML)', 'Neither'))
    
    disagreements.to_csv('results/disagreements.csv', index=False)
    
    plt.style.use('dark_background')
    
    # Plot 1: Detection vs Intercept
    plt.figure(figsize=(8,5))
    grouped = test_df1[test_df1['attack']==True].groupby('eve')[['RuleA_reject', 'RuleB_reject']].mean() * 100
    plt.plot(grouped.index * 100, grouped['RuleA_reject'], marker='o', label='Rule A (11% QBER)')
    plt.plot(grouped.index * 100, grouped['RuleB_reject'], marker='s', label='Rule B (ML)')
    plt.xlabel('Intercept Fraction (%)')
    plt.ylabel('Detection Rate (%)')
    plt.title('Detection Rate vs Eve Intercept Fraction (Held-out Test)')
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig('results/detection_vs_intercept.png', transparent=True)
    plt.close()
    
    # Plot 2: FA vs Noise
    plt.figure(figsize=(8,5))
    grouped_fa = test_df1[test_df1['attack']==False].groupby('noise')[['RuleA_reject', 'RuleB_reject']].mean() * 100
    plt.plot(grouped_fa.index * 100, grouped_fa['RuleA_reject'], marker='o', label='Rule A')
    plt.plot(grouped_fa.index * 100, grouped_fa['RuleB_reject'], marker='s', label='Rule B')
    plt.xlabel('Channel Noise (%)')
    plt.ylabel('False Alarm Rate (%)')
    plt.title('False Alarm Rate vs Channel Noise (Held-out Test)')
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig('results/fa_vs_noise.png', transparent=True)
    plt.close()
    
    # Plot 3: Confusion Matrix
    plt.figure(figsize=(6,5))
    cm = confusion_matrix(test_df1['attack'], test_df1['RuleA_reject'])
    plt.imshow(cm, interpolation='nearest', cmap='Blues')
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ['Accepted', 'Rejected'])
    plt.yticks(tick_marks, ['Honest', 'Attacked'])
    plt.xlabel('Rule A Verdict')
    plt.ylabel('Ground Truth')
    plt.title('Confusion Matrix (Rule A)')
    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(cm[i, j]), horizontalalignment="center",
                     color="white" if cm[i, j] > cm.max() / 2. else "black")
    plt.tight_layout()
    plt.savefig('results/confusion_matrix.png', transparent=True)
    plt.close()
    
    with open('results/README.md', 'w') as f:
        f.write("# ML Evaluation Results\n\n")
        f.write("Generated by `evaluate.py`.\n")
        f.write("- **Qubits per run**: 1000\n")
        f.write(f"- **Total sessions**: {len(df)}\n")
        f.write(f"- **ML Threshold (p1, p2)**: {p1:.2f}, {p2:.2f}\n")

if __name__ == '__main__':
    main()
