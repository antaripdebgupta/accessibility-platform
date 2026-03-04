# Firebase Configuration Guide

## Problem
Firebase shows `Error (auth/invalid-api-key)` in Docker because Vite embeds environment variables at **build time**, not runtime. If your `.env` file contains placeholder values like `your-firebase-api-key`, those get baked into the production build.

## Solution

### Step 1: Get Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create one)
3. Go to **Project Settings** → **General**
4. Scroll to **Your apps** section
5. Copy these values:
   - API Key
   - Auth Domain
   - Project ID
   - App ID

### Step 2: Update .env File

Edit your `.env` file with **real values**:

```bash
# Replace with actual values from Firebase Console
VITE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef123456
VITE_USE_FIREBASE_EMULATOR=false
```

### Step 3: Rebuild Docker Image

The frontend Docker image must be rebuilt to embed the new values:

```bash
# Stop and remove old containers
docker compose down

# Rebuild frontend with --no-cache to ensure fresh build
docker compose build --no-cache frontend

# Start services
docker compose up -d
```

Or use the shortcut:
```bash
make down
make up
```

## Important Notes

- **VITE_* variables are embedded at build time** - changing `.env` requires rebuilding the Docker image
- Never commit `.env` with real credentials (it's in `.gitignore`)
- For production deployments, use CI/CD secrets or environment-specific `.env` files
- The `npm run dev` works because Vite dev server reads `.env` at runtime

## Verification

After rebuilding, check the browser console:
- Should NOT see `Error (auth/invalid-api-key)`
- Should see Firebase initialized successfully
- Check Network tab for Firebase API calls (should return 200, not 400)

## Development vs Production

- **Development** (`npm run dev`): Reads `.env` at runtime ✓
- **Docker Production**: Reads `.env` at build time, requires rebuild ✓
