Why: order batching is a VRP (vehicle routing problem) with an ML predicted cost input (prep time), not a pure OR toy problem — that's the whole value.

Architecture
ML: predict prep time per order (features: item count, item, hour, store load)
OR: cluster+route orders into rider trips — OR-Tools VRP, minimize total time under rider-capacity + delivery-window constraints
API: FastAPI, /batch endpoint — orders in, rider assignments + routes out
Docker → Render, Streamlit map view showing batches

Data: no public quick-commerce dataset exists. Simplest path is to simulate. simulate: random store location, ~50-200 synthetic orders/hour with lat/lng, prep-time label from a formula + noise.