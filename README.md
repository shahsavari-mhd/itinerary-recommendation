# Travel Itinerary Generator

A serverless travel itinerary generator that creates personalized travel plans using AI. Built with Cloudflare Workers, Firebase, and LLM integration.

## Features

- **AI-Powered Planning**: Generate detailed travel itineraries using advanced language models
- **Asynchronous Processing**: Handle itinerary generation in the background for optimal user experience
- **Persistent Storage**: Store and retrieve itineraries using Firebase Firestore
- **RESTful API**: Clean, well-documented endpoints for easy integration
- **Serverless Architecture**: Deploy globally with Cloudflare Workers for low latency

##  Architecture

### Technology Stack
- **Runtime**: Cloudflare Workers (Edge computing)
- **Database**: Firebase Firestore (NoSQL document database)
- **Authentication**: Firebase Auth (Email/Password)
- **AI Integration**: OpenAI API
- **Language**: Python

### Design Patterns
The project follows a clean architecture approach with clear separation of concerns:

**Services Layer**: Business logic for domain-specific operations
- `ItineraryService`: Handles itinerary creation, generation, and retrieval logic

**Repository Layer**: Data access abstraction
- `ItineraryRepository`: Encapsulates Firebase Firestore operations for itineraries

**Utils Layer**: Shared utilities and helpers
- Authentication helpers
- Data validation utilities
- Error handling utilities

## Setup Instructions

### Prerequisites
- Node.js (v18+)
- Wrangler CLI (`npm install -g wrangler`)
- Firebase account
- Google Cloud Console access
- OpenAI API account

### 1. Environment Variables Setup
- environment variable setup (e.g., for Firebase service account credentials and your LLM API key).
- generate firebase api key from google cloud console (https://console.cloud.google.com) -> APIs & Services -> Credentials -> Create Credentials (alongside Credentials title, top of API Keys list) -> API Key
- to develop locally copy .dev.vars.example to .dev.vars and set those variables
- in firebase to access and auth from cloudflare worker 
    - go to firebase -> authentication -> sign-in method -> add provider -> enable email/password 
    - go to firebase -> authentication -> add user
- get firebase project id and firebase api key from firebase -> project settings (alongside project overview top left) -> general tab

#### For Local Development
1. Copy the example environment file:
   ```bash
   cp .dev.vars.example .dev.vars
   ```

2. Fill in your `.dev.vars` file with the following variables:
   ```bash
   # [ENTER YOUR LLM API KEY HERE]
   LLM_API_KEY=your_llm_api_key_here
   
   # [ENTER YOUR FIREBASE CREDENTIALS HERE]
   FIREBASE_EMAIL=your_firebase_user_email
   FIREBASE_PASSWORD=your_firebase_user_password
   FIREBASE_API_KEY=your_firebase_web_api_key
   FIREBASE_PROJECT_ID=your_firebase_project_id
   
   # [ENTER YOUR FIRESTORE COLLECTION NAME HERE]
   FIRESTORE_COLLECTION=itineraries
   ```

#### For Production Deployment
Set these same variables as Cloudflare Worker secrets:
```bash
npx wrangler secret put LLM_API_KEY
npx wrangler secret put FIREBASE_EMAIL
npx wrangler secret put FIREBASE_PASSWORD
npx wrangler secret put FIREBASE_API_KEY
npx wrangler secret put FIREBASE_PROJECT_ID
npx wrangler secret put FIRESTORE_COLLECTION
```

### 2. Firebase Configuration

#### Get Firebase Project ID and API Key
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create a new one)
3. Navigate to **Project Settings** (gear icon next to "Project Overview")
4. In the **General** tab, copy:
   - **Project ID** → Use as `FIREBASE_PROJECT_ID`
   - **Web API Key** → Use as `FIREBASE_API_KEY`

#### Enable Authentication
1. Go to **Authentication** → **Sign-in method**
2. Click **Add new provider**
3. Enable **Email/Password** authentication
4. Go to **Authentication** → **Users**
5. Click **Add user** and create a user account
6. Use this email/password as `FIREBASE_EMAIL` and `FIREBASE_PASSWORD`

#### Set up Firestore Database
1. Go to **Firestore Database**
2. Click **Create database**
3. Choose **Start in production mode** (or test mode for development)
4. Select your preferred region
5. The collection will be created automatically when first itinerary is saved

### 3. LLM API Setup
- Sign up for [YOUR_LLM_PROVIDER] account
- Generate API key from dashboard
- Copy key to environment variables

## 🚀 Running the Project

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npx wrangler dev
```

The API will be available at `http://localhost:8787`

### Production Deployment
```bash
# Deploy to Cloudflare Workers
npx wrangler deploy
```

Your API will be deployed to: `https://[YOUR_WORKER_NAME].[YOUR_SUBDOMAIN].workers.dev`

## 📡 API Documentation

### Base URL
- **Local**: `http://localhost:8787`
- **Production**: `https://[YOUR_DEPLOYED_URL].workers.dev`

### Endpoints

#### Create Itinerary Request
Creates a new itinerary generation request and returns an ID for tracking.

**POST** `/create`

**Request Body:**
```json
{
  "destination": "string",
  "durationDays": "number"
}
```

**Response:**
```json
{
  "success": true,
  "id": "Mv8XOWZmDl15xfnvhZst",
  "message": "Itinerary generation started"
}
```

**Example:**
```bash
curl --header "Content-Type: application/json" \
     --request POST \
     --data '{"destination": "Tokyo, Japan", "duration_days": 7}' \
     http://localhost:8787/create
```

#### Get Generated Itinerary
Retrieves a generated itinerary by ID.

**GET** `/itinerary?id={id}`

**Response (Pending):**
```json
{
  "success": false,
  "status": "generating",
  "message": "Itinerary is still being generated"
}
```

**Response (Complete):**
```json
{
  "success": true,
  "status": "completed",
  "data": {
    "destination": "Tokyo, Japan",
    "duration_days": 7,
    "itinerary": {
      // Generated itinerary content
    }
  }
}
```

**Example:**
```bash
curl --header "Content-Type: application/json" \
     --request GET \
     "http://localhost:8787/itinerary?id=Mv8XOWZmDl15xfnvhZst"
```

### Error Responses
```json
{
  "success": false,
  "error": "Error message description",
}
```

## 🤖 Prompt Engineering

### Design Principles
The LLM prompt is designed with the following principles:

**Role Definition**: Clear system role as a professional travel planner with extensive worldwide knowledge
```
You are a professional travel planner with expertise in creating detailed, practical itineraries.
```
**Strict Output Format**: Enforces pure JSON response without explanations using the directive: `"dont include any explanations or additional text outside the JSON format"`

**Structured Schema**: Consistent JSON array format with themed daily activities:
```json
[
  {
    "day": 1,
    "theme": "Descriptive theme for the day",
    "activities": [
      {
        "time": "Morning/Afternoon/Evening",
        "description": "Detailed activity description with practical tips",
        "location": "Specific location name"
      }
    ]
  }
]
```

**Comprehensive Guidelines**: The prompt includes detailed instructions for:
- **Thematic Organization**: Each day has a coherent theme (Historical Exploration, Cultural Immersion, etc.)
- **Time Management**: Consistent Morning/Afternoon/Evening time slots
- **Practical Details**: Booking advice, duration estimates, insider tips
- **Geographical Logic**: Minimizing travel time with logical location flow
- **Cultural Sensitivity**: Considering local customs, seasons, and opening hours
- **Activity Balance**: Mix of must-see attractions, local experiences, paid and free activities

**Contextual Considerations**: 
- Seasonal factors and peak tourism periods
- Local cultural customs and etiquette
- Practical travel logistics (opening hours, distances)
- Weather contingency planning
- Dining recommendations integration
- Rest periods and realistic timing

### Complete Prompt Template
read from src/prompts/itineraries_prompt.py
```
You are a professional travel planner with extensive knowledge of destinations worldwide. Your task is to create detailed, practical itineraries based on user inputs.

## Instructions:
Create a complete travel itinerary in JSON format based on the provided destination and duration. Consider local culture, popular attractions, practical travel times, seasonal factors, and create a logical flow between activities. 
**dont include any explanations or additional text outside the JSON format**

## Input Format:
- **Destination**: [Location/City/Country]
- **Duration**: [Number of days]

## Output Requirements:
Generate a JSON array following this exact schema:
[Schema details as shown above...]

## Guidelines:
1. **Day Themes**: Each day should have a coherent theme
2. **Time Slots**: Use "Morning", "Afternoon", and "Evening" consistently
3. **Descriptions**: Include practical details like booking advice, duration estimates, or insider tips
4. **Locations**: Use specific, recognizable location names
5. **Flow**: Ensure logical geographical progression to minimize travel time
6. **Balance**: Mix must-see attractions with local experiences
7. **Practicality**: Consider opening hours, travel distances, and realistic timing

## Additional Considerations:
- Include dining recommendations when appropriate
- Account for rest periods and travel time between locations
- Suggest backup indoor activities for potential weather issues
- Consider the destination's peak seasons and local customs
- Include a mix of paid attractions and free activities

**Destination:** {{destination}}
**Duration:** {{duration}}
```

## 🧪 Testing

### Manual Testing
Use the provided curl examples to test both endpoints:

1. Create an itinerary request
2. Wait a few seconds for generation
3. Retrieve the completed itinerary

### Expected Flow
1. **POST** `/create` → Returns `id`
2. **GET** `/itinerary?id={id}` → Initially returns "generating" status
3. **GET** `/itinerary?id={id}` → Eventually returns completed itinerary

---

**Note**: This project was created as part of a technical interview process, demonstrating serverless architecture, API design, and AI integration capabilities.