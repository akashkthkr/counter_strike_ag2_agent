# Counter-Strike AG2 Preview UI

This directory contains the static preview UI that gets deployed to Cloudflare Pages for live previews of the Counter-Strike AG2 Agent System.

## 🚀 Live Preview

The preview UI is automatically deployed to Cloudflare Pages on every push:
- **Production:** [https://counter-strike-ag2-preview.pages.dev](https://counter-strike-ag2-preview.pages.dev)
- **Pull Request Previews:** Automatically generated for each PR

## 🎮 Features

### Interactive Demo
- **Real-time Connection:** Connect to any deployed backend instance
- **Agent Panels:** 3 Terrorist agents + 1 CT commander interface
- **WebSocket Support:** Real-time game state updates
- **Quick Actions:** Pre-configured demo actions for testing

### Backend Integration
- **Flexible Backend URL:** Connect to any deployed instance
- **Health Checks:** Automatic backend connectivity testing  
- **Session Management:** Automatic game session creation
- **WebSocket Communication:** Real-time bidirectional communication

### Demo Controls
- **Strategy Queries:** Test RAG system with "what should we do?" queries
- **Game Actions:** Plant bomb, defuse, shoot, move commands
- **Status Monitoring:** Real-time game state display
- **Connection Management:** Connect/disconnect/reset functionality

## 🛠️ Development

### Local Development
```bash
# Serve the preview locally
cd preview-ui
npm install
npm run dev
# Visit http://localhost:8080
```

### Building for Production
```bash
npm run build
# Output goes to dist/ directory
```

## 🔧 Configuration

### Backend Connection
1. Deploy your backend using Docker compose or cloud deployment
2. Update the backend URL in the preview UI
3. The preview will automatically:
   - Test backend connectivity
   - Create a game session
   - Establish WebSocket connection
   - Enable real-time interactions

### Cloudflare Pages Setup
The GitHub workflow automatically handles deployment, but for manual setup:

1. **Create Cloudflare Pages project:**
   - Connect to your GitHub repository
   - Set build command: `npm run build`
   - Set output directory: `dist`

2. **Environment Variables:**
   - `BACKEND_URL`: Your deployed backend URL
   - `CLOUDFLARE_API_TOKEN`: For automatic deployment
   - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare account ID

## 🎯 Usage

### For Development
1. **Deploy Backend:** Use `docker compose up` or deploy to cloud
2. **Open Preview:** Visit the Cloudflare Pages URL
3. **Connect:** Enter your backend URL and click "Connect"
4. **Test:** Use demo controls or agent panels

### For Demonstrations
1. **Share Preview URL:** Send the Cloudflare Pages link
2. **Provide Backend URL:** Share your deployed backend URL
3. **Guide Users:** 
   - Connect to backend
   - Try quick actions
   - Use agent panels for custom commands

## 📊 Monitoring

### Connection Status
- **Green:** Connected to backend with active WebSocket
- **Red:** Disconnected or backend unavailable
- **Health Checks:** Automatic backend API health monitoring

### Game State Display
- **Round Information:** Current round and timer
- **Bomb Status:** Planted/defused status
- **Team Scores:** Real-time score updates
- **Agent Logs:** Individual agent response history

## 🚨 Troubleshooting

### Connection Issues
- **CORS Errors:** Ensure backend allows preview domain
- **WebSocket Failures:** Check backend WebSocket endpoint
- **Health Check Fails:** Verify backend `/health` endpoint

### Common Solutions
1. **Backend URL Format:** Include `http://` or `https://`
2. **Firewall/Proxy:** Ensure WebSocket connections allowed
3. **SSL/TLS:** Use HTTPS backends for HTTPS preview sites

## 🔄 Deployment Workflow

### Automatic Deployment
1. **Push to GitHub:** Triggers workflow
2. **Build Preview:** Creates static files
3. **Deploy to Cloudflare:** Automatic deployment
4. **PR Comments:** Preview URLs added to pull requests

### Manual Deployment
```bash
# Build locally
npm run build

# Deploy to Cloudflare Pages
npx wrangler pages publish dist --project-name=counter-strike-ag2-preview
```

## 🔗 Integration Points

### Backend API Endpoints
- `GET /health` - Backend health check
- `POST /game/create` - Create game session
- `POST /game/{session_id}/action` - Send game actions
- `WebSocket /ws/{session_id}` - Real-time updates

### Frontend Components
- **Connection Manager:** Backend connectivity handling
- **Agent Panels:** Individual agent interfaces
- **Game State Display:** Real-time status updates
- **Demo Controls:** Quick action buttons

This preview UI provides a complete demonstration environment for the Counter-Strike AG2 system, allowing users to interact with the multi-agent system through an intuitive web interface.
