# Intelligent-Emergency-Response-Route-Optimization

## Getting Started (Codespaces / Dev Container)

This project consists of three pieces:

1. **ai-engine** – Python/FastAPI service listening on **port 8000**.
2. **server** – Node/Express orchestrator on **port 5000**.
3. **client** – React/Vite dashboard that talks to the orchestrator.

### Opening ports in Codespaces

When running inside GitHub Codespaces the ports are not public by default. If
you start the server (`npm run dev` in `server`), you **must** expose port
`5000`:

- Click the **Ports** tab in the Codespaces sidebar.
- Locate `5000` in the list (it may be marked "closed").
- Set its visibility to **Public** (or click the button labelled "Make public").

The UI will then be available at a URL such as
`https://<workspace>-5000.app.github.dev`.

If you forget to make port 5000 public the frontend will show an alert:

```
CONNECTION_FAILURE: Ensure Port 5000 is PUBLIC in the Ports tab.
```

### Configuring the frontend

Copy the public URL from the Ports panel into a `.env` file in the `client`
folder:

```
VITE_BASE_URL=https://opulent-system-5gxxpqvjrw9vfppwv-5000.app.github.dev
```

Restart the Vite server so the variable is picked up (`npm run dev` inside
`client`).  The React app will fall back to `http://localhost:5000` when run
outside of Codespaces.

---
