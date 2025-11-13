# **Locsent: GPS Tracking Dashboard**

[![Status](https://img.shields.io/badge/Status-Live-brightgreen)](https://locsent.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Deployment](https://img.shields.io/badge/Deployment-Vercel-blue?logo=vercel)](https://vercel.com/)

A modern, role-based web dashboard built with Python and Flask to monitor user GPS coordinates in real-time. Locsent provides secure access for admins and users, logs location history, and uniquely utilizes Notion as a powerful, serverless backend.

---
## ↗️ Live Demo: [locsent.vercel.app](https://locsent.vercel.app)

<table align="center">
  <tr>
    <td style="border: 2px solid #ccc; border-radius: 10px; padding: 5px;">
      <img src="https://github.com/user-attachments/assets/e23da6cb-1b4c-4eff-9e93-dcd88935c262" 
           alt="Long Node Screenshot" width="100%">
    </td>
  </tr>
</table>

---

## Core Features

-   **Live Interactive Map**: Admins see all users on a single map, updating in real-time. Users see their own location on a personal map.
-   **Role-Based Access Control**: Secure login system for `Admin` and `User` roles.
-   **Admin Monitoring Dashboard**:
    -   View, manage, and **delete** registered users.
    -   Fetch a user's location history, including **IP Address**, **Device Info**, and **Battery Status**.
    -   **Export** any user's complete location history as CSV, HTML, or PDF.
    -   Open any coordinate directly in **Google Maps**.
-   **Geofencing**: Admins can define safe zones in Notion. The system will flash an alert on the dashboard if a user sends a location from inside a defined zone.
-   **Dynamic Admin Controls**:
    -   **Enable or Disable public sign-ups** with the click of a button to secure your application.
-   **Notion as a Database**: All user, location, geofence, and application settings data is stored and managed in a Notion workspace.
-   **Modern UI/UX**:
    -   Clean, animated, and fully responsive design with a glassmorphism header.
    -   Supports both **Dark Mode** and **Light Mode**.

---

## How to Use the Application

This guide explains how to use Locsent once it has been set up and is running.

### For Administrators

1.  **Login**: Use the admin credentials you created manually in the `Users` Notion database.
2.  **View the Live Map**: The main map on your dashboard shows the last known location of all registered users. Markers update automatically.
3.  **Manage Geofences**: To add, edit, or remove a geofence, simply edit the rows in your `Geofences` database in Notion. The map will reflect these changes automatically.
4.  **Control User Sign-Up**: In the "Admin Controls" panel, you can click the "Enable/Disable Sign-Up" button to control whether new users can register.
5.  **Manage Users**:
    *   **View History**: Click the "History" button next to any user to see their last 10 location logs, latest coordinates, and device info.
    *   **Export Data**: Click the "Export" button and choose a format (CSV, HTML, PDF) to download a user's complete location history.
    *   **Delete User**: Click the "Delete" button. You will be asked for confirmation before the user is permanently removed.

### For Users

1.  **Sign Up**: If enabled by the admin, new users can create an account on the sign-up page.
2.  **Login**: Use your registered credentials to access the dashboard.
3.  **View Your Map**: Your dashboard features a personal map showing your current location and all the geofence zones defined by the administrator. Your marker will update periodically.
4.  **Send Location Manually**: Click the "Send Current Location" button to immediately log your coordinates and send them to the admin.
5.  **Automatic Tracking**: Your location is also sent automatically in the background every hour while you are logged in.

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python, Flask, Flask-Login, Flask-Bcrypt, Flask-WTF |
| **Database** | Notion API |
| **Frontend** | HTML, CSS, JavaScript, Leaflet.js |
| **PDF Generation** | FPDF2 |
| **Deployment** | Vercel |

---

## Project Structure

The project uses the Application Factory pattern with all Python files in the root for simplicity and to prevent import errors.

```
Locsent/
├── .env
├── .gitignore
├── README.md
├── app.py              # The Application Factory
├── auth.py             # Manages authentication 
├── build.sh            # Essential requirements for vercel 
├── decorators.py       # Custom decorators 
├── extensions.py       # Initializes extensions
├── models.py           # Handles all communication with the Notion API
├── requirements.txt    # Python package dependencies
├── routes.py           # Defines application routes and view logic
├── run.py              # The entry point to run the application
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── admin_dashboard.html
│   ├── export_template.html
│   ├── layout.html
│   ├── login.html
│   ├── signup.html
│   └── user_dashboard.html
└── vercel.json
```

---

## Getting Started

Follow these instructions to get a local copy up and running.

### 1. Notion Setup (The Backend)

Your Notion workspace will act as your database. This is a critical step.

#### **A. Create a Notion Integration**
1.  Go to [notion.so/my-integrations](https://www.notion.so/my-integrations).
2.  Click **"+ New integration"**. Name it "Locsent API".
3.  Copy the **"Internal Integration Token"**. This is your `NOTION_API_KEY`.

#### **B. Create Four Notion Databases**
Create four new, empty databases in your Notion workspace with the **exact properties** shown below.

### **1. `Users` Database**
| Property Name | Property Type |
| :--- | :--- |
| `UserID` | **Title** |
| `Username`| **Text** |
| `Role` | **Select** |
| `PasswordHash` | **Text** |

### **2. `Location_History` Database**
| Property Name | Property Type |
| :--- | :--- |
| `LogID` | **Title** |
| `User` | **Relation** (linked to `Users` db) |
| `Timestamp`| **Date** |
| `Latitude` | **Number** |
| `Longitude`| **Number** |
| `IPAddress`| **Text** |
| `Battery` | **Text** |
| `DeviceInfo`| **Text** |

### **3. `Geofences` Database**
| Property Name | Property Type |
| :--- | :--- |
| `Name` | **Title** |
| `Latitude` | **Number** |
| `Longitude`| **Number** |
| `Radius` | **Number** |

### **4. `AppSettings` Database**
| Property Name | Property Type |
| :--- | :--- |
| `Setting` | **Title** |
| `Value` | **Text** |

*After creating it, add one row: `Setting` = **`SignUpEnabled`**, `Value` = **`true`***

#### **C. Connect Your Integration to ALL Four Databases**
You must give your API key permission to access each database.
1.  Open the `Users` database page.
2.  Click the `...` menu in the top-right corner.
3.  Click **"Add connections"** and search for your "Locsent API" integration.
4.  **Repeat these steps for `Location_History`, `Geofences`, and `AppSettings` databases.**

#### **D. Get Your Database IDs**
1.  Open each database page. The ID is in the URL: `notion.so/`**`DATABASE_ID`**`?v=...`
2.  Copy the IDs for all four databases.

---

### 2. Local Project Setup

#### **A. Clone the Repository**
```bash
git clone https://github.com/krupal-036/Locsent.git
cd Locsent
```

#### **B. Create and Activate a Virtual Environment**
```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### **C. Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **D. Set Up Environment Variables**
1.  Create a file in the root directory named `.env`.
2.  Fill it with your keys and IDs.

```env
# .env file
FLASK_SECRET_KEY='generate_a_long_random_string_for_security'
NOTION_API_KEY='secret_...'
NOTION_DATABASE_ID_USERS='your_users_database_id'
NOTION_DATABASE_ID_LOCATIONS='your_locations_database_id'
NOTION_DATABASE_ID_GEOFENCES='your_geofences_database_id'
NOTION_DATABASE_ID_SETTINGS='your_appsettings_database_id'
```

#### **E. Create Your First Admin User**
1.  You must manually add your first `Admin` user in your Notion `Users` database.
2.  To generate a secure password hash, create a temporary Python file (`hash_generator.py`) and run it:
    ```python
    # hash_generator.py
    from flask_bcrypt import Bcrypt
    password_to_hash = 'your_strong_admin_password'
    hashed_password = Bcrypt().generate_password_hash(password_to_hash).decode('utf-8')
    print(f'Your hashed password is:\n{hashed_password}')
    ```
    ```bash
    python hash_generator.py
    ```
3.  Copy the resulting hash into the `PasswordHash` column in Notion. Set the `Role` to `Admin`.

### 3. Run the Application
```bash
python run.py
```
The application will be available at `http://127.0.0.1:5000`.

---

## Deployment

This application is configured for easy deployment on **Vercel**.

1.  Push your project to your GitHub repository.
2.  Go to your [Vercel Dashboard](https://vercel.com/) and import your `Locsent` repository.
3.  In the project settings on Vercel, go to **"Environment Variables"** and add the same key-value pairs from your `.env` file.
4.  Click **"Deploy"**. Your application will be live!

---

## License

This project is licensed under the **MIT License** — feel free to use and modify it.

---

## Contact

Developed by [Krupal Fataniya](https://krupal.vercel.app/)

Feel free to contribute or fork the project!

For any issues, feel free to ask [Krupal](mailto:krupalfataniya007@gmail.com). 😊 
