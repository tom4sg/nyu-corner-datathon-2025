# Vibe Search Frontend

A modern Next.js frontend for the Vibe Search application that helps NYU students find the best venues and study spots.

## Features

- 🎨 Modern, responsive UI with Tailwind CSS
- 🔍 Real-time search with suggestions
- 📱 Mobile-friendly design
- ⚡ Fast loading with Next.js
- 🎯 TypeScript for better development experience

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
Create a `.env.local` file in the frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Deployment

### Vercel Deployment

1. Connect your GitHub repository to Vercel
2. Set the **Root Directory** to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = Your Railway backend URL
4. Deploy!

### Environment Variables

- `NEXT_PUBLIC_API_URL`: The URL of your Railway backend API

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   └── page.tsx          # Main page component
│   ├── components/
│   │   ├── SearchBox.tsx     # Search input component
│   │   └── ResultsList.tsx   # Results display component
│   └── types/
│       └── place.ts          # TypeScript type definitions
├── vercel.json               # Vercel configuration
└── package.json
```

## API Integration

The frontend connects to your FastAPI backend running on Railway. Make sure to:

1. Deploy your backend to Railway first
2. Update `NEXT_PUBLIC_API_URL` with your Railway URL
3. Ensure CORS is properly configured on your backend

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
