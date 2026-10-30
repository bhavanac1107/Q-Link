# Q-Link Dataset Sources

## Satellite QKD Modeled Dataset (Decoy-BB84 & BBM92)

- **Source / Repository**: Zenodo
- **DOI**: [10.5281/zenodo.14054879](https://doi.org/10.5281/zenodo.14054879)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Nature of Data**: **MODELED data** (computational orbit, atmospheric channel, and QKD simulation), **not** experimentally measured physical data.
- **Protocols Covered**:
  - `DV_Protocol`: Decoy-BB84 for GEO, LEO, and MEO orbits.
  - `ENT_protocol`: BBM92 Entanglement-based QKD for dual ground stations (Helmos & Matera).
- **Attributes**:
  - `qber`: Quantum Bit Error Rate modeled under atmospheric turbulence and background noise.
  - `key_rate`: Secret Key Rate (bps).
  - `link_loss_db`: Channel optical loss in decibels.
  - `distance_km`: `None` (omitted for orbital geometry to avoid synthetic estimation).
  - `data_source`: Marked strictly as `"modeled"` across all records.
