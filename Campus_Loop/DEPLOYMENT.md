# 🚀 Campus Loop Deployment Guide

This guide will help you deploy your Campus Loop Django project to various platforms.

## 📋 Prerequisites

1. **Git repository** - Your project should be in a Git repository
2. **Python 3.12** - Make sure you have Python 3.12 installed
3. **Django project** - Your project should be working locally

## 🎯 Quick Deploy Options

### Option 1: Railway (Recommended - Free)

**Railway** is perfect for Django projects and offers a generous free tier.

#### Step 1: Prepare Your Project
```bash
# Make sure all files are committed to Git
git add .
git commit -m "Prepare for deployment"
```

#### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your Campus Loop repository
5. Railway will automatically detect it's a Django project

#### Step 3: Configure Environment Variables
In Railway dashboard, add these environment variables:
```
DEBUG=False
SECRET_KEY=your-secret-key-here
```

#### Step 4: Deploy
Railway will automatically:
- Install dependencies from `requirements.txt`
- Run migrations
- Start your application

Your app will be available at: `https://your-app-name.railway.app`

---

### Option 2: Render (Free Tier)

**Render** is another excellent free option for Django deployment.

#### Step 1: Prepare Your Project
```bash
# Make sure all files are committed to Git
git add .
git commit -m "Prepare for deployment"
```

#### Step 2: Deploy to Render
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: campus-loop
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn CampusLoop.wsgi:application`

#### Step 3: Add Environment Variables
```
DEBUG=False
SECRET_KEY=your-secret-key-here
```

Your app will be available at: `https://your-app-name.onrender.com`

---

### Option 3: DigitalOcean App Platform ($5/month)

**DigitalOcean** offers reliable hosting with a simple setup.

#### Step 1: Prepare Your Project
```bash
# Make sure all files are committed to Git
git add .
git commit -m "Prepare for deployment"
```

#### Step 2: Deploy to DigitalOcean
1. Go to [digitalocean.com](https://digitalocean.com)
2. Create an account
3. Go to "Apps" → "Create App"
4. Connect your GitHub repository
5. Configure:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn CampusLoop.wsgi:application`

#### Step 3: Add Environment Variables
```
DEBUG=False
SECRET_KEY=your-secret-key-here
```

---

## 🔧 Manual Deployment Steps

### Step 1: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 2: Run Migrations
```bash
python manage.py migrate
```

### Step 3: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 4: Set Environment Variables
```bash
export DEBUG=False
export SECRET_KEY=your-secret-key-here
```

### Step 5: Start the Server
```bash
gunicorn CampusLoop.wsgi:application
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Set `DEBUG=False`
- [ ] Generate a new `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Set up HTTPS (most platforms do this automatically)
- [ ] Configure database (SQLite for small apps, PostgreSQL for larger ones)
- [ ] Set up proper logging
- [ ] Configure static file serving

---

## 📊 Database Options

### SQLite (Default - Good for small apps)
- Already configured
- Good for up to 1000 users
- No additional setup needed

### PostgreSQL (Recommended for production)
1. Install PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

2. Update `settings_production.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## 🚨 Troubleshooting

### Common Issues:

1. **Static files not loading**
   - Make sure `whitenoise` is in `MIDDLEWARE`
   - Run `python manage.py collectstatic`

2. **Database errors**
   - Run `python manage.py migrate`
   - Check database connection settings

3. **Import errors**
   - Make sure all packages are in `requirements.txt`
   - Check Python version compatibility

4. **Environment variables**
   - Verify all required env vars are set
   - Check for typos in variable names

---

## 📞 Support

If you encounter issues:

1. Check the deployment platform's logs
2. Verify all environment variables are set
3. Test locally with production settings
4. Check Django's deployment checklist

---

## 🎉 Success!

Once deployed, your Campus Loop application will be available online for students to:
- Buy and sell items
- Share academic resources
- Connect with other students
- Manage bookings and messages

**Happy Deploying! 🚀** 