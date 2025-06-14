# Elite Autonomous Trading Platform - Deployment Guide

## 🚀 DigitalOcean App Platform Deployment

This guide will help you deploy the Elite Autonomous Trading Platform on DigitalOcean App Platform with dedicated PostgreSQL and Redis databases.

### Prerequisites

1. **DigitalOcean Account** with App Platform access
2. **GitHub Repository** with your code
3. **Dedicated PostgreSQL Database** on DigitalOcean
4. **Dedicated Redis Database** on DigitalOcean
5. **DigitalOcean CLI** (doctl) installed
6. **Trading API Credentials** (TrueData, Zerodha)

### Step 1: Prepare Your Repository

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Production deployment ready"
   git push origin main
   ```

2. **Update app.yaml:**
   - Edit `.do/app.yaml`
   - Replace `YOUR_GITHUB_USERNAME/elite-trading-platform` with your actual repository

### Step 2: Set Up Databases

#### PostgreSQL Database
1. Create a PostgreSQL database in DigitalOcean
2. Note the connection details:
   - Host, Port, Database name, Username, Password
3. Connection string format:
   ```
   postgresql://username:password@host:port/database_name
   ```

#### Redis Database
1. Create a Redis database in DigitalOcean
2. Note the connection details:
   - Host, Port, Password (if any)
3. Connection string format:
   ```
   redis://username:password@host:port
   ```

### Step 3: Configure Environment Variables

In DigitalOcean App Platform dashboard, set these environment variables:

#### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@host:port/database_name
REDIS_URL=redis://username:password@host:port
```

#### Security Configuration
```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-for-production
```

#### Trading API Credentials
```bash
TRUEDATA_USERNAME=your_truedata_username
TRUEDATA_PASSWORD=your_truedata_password
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_API_SECRET=your_zerodha_api_secret
ZERODHA_CLIENT_ID=your_zerodha_client_id
```

### Step 4: Deploy Using App Platform

#### Option A: Using DigitalOcean Dashboard

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect your GitHub repository
4. Upload the `.do/app.yaml` file
5. Review and configure environment variables
6. Deploy the app

#### Option B: Using CLI

1. **Install doctl:**
   ```bash
   # On macOS
   brew install doctl
   
   # On Linux
   wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz
   tar xf doctl-1.104.0-linux-amd64.tar.gz
   sudo mv doctl /usr/local/bin
   ```

2. **Authenticate:**
   ```bash
   doctl auth init
   ```

3. **Deploy:**
   ```bash
   doctl apps create --spec .do/app.yaml
   ```

### Step 5: Configure GitHub Actions (CI/CD)

1. **Set GitHub Secrets:**
   Go to your repository → Settings → Secrets and variables → Actions

   Add these secrets:
   ```
   DIGITALOCEAN_ACCESS_TOKEN=your_do_access_token
   ```

2. **Enable GitHub Actions:**
   - The workflow is already configured in `.github/workflows/deploy.yml`
   - Push to `main` branch triggers deployment

### Step 6: Database Migration

After deployment, the database schema will be automatically created. If you need to migrate existing data:

1. **Connect to your PostgreSQL database**
2. **Run migrations if needed**
3. **Verify schema creation in logs**

### Step 7: Post-Deployment Configuration

#### Domain Configuration
1. In App Platform dashboard, configure your custom domain
2. SSL certificates are automatically managed

#### Health Checks
- Health check endpoint: `/health`
- API health check: `/api/health`

#### Monitoring
- Check App Platform logs for any issues
- Monitor database connections
- Verify Redis cache connectivity

### Step 8: Production Checklist

#### Security
- [ ] JWT secret key configured
- [ ] Database credentials secured
- [ ] API credentials configured
- [ ] CORS origins configured for production domain

#### Performance
- [ ] Database indexes created
- [ ] Redis cache working
- [ ] Health checks passing
- [ ] Load testing completed

#### Trading Configuration
- [ ] Paper trading disabled (`PAPER_TRADING=false`)
- [ ] Trading APIs connected
- [ ] Risk management configured
- [ ] Stop loss percentages set

#### Monitoring
- [ ] Application logs monitored
- [ ] Database performance monitored
- [ ] Error tracking configured
- [ ] Alerts set up for failures

### Environment Variables Reference

#### Required Production Variables
```bash
# Database
DATABASE_URL=postgresql://username:password@host:port/database_name
REDIS_URL=redis://username:password@host:port

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key

# Trading APIs
TRUEDATA_USERNAME=your_username
TRUEDATA_PASSWORD=your_password
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_CLIENT_ID=your_client_id
```

#### Optional Configuration Variables
```bash
# Trading Configuration
PAPER_TRADING=false
DAILY_STOP_LOSS_PERCENT=2.0
AUTO_SQUARE_OFF_ENABLED=true

# Performance
WORKERS=1
MAX_REQUESTS=1000
TIMEOUT=300

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

### Troubleshooting

#### Common Issues

1. **Database Connection Failed**
   - Verify DATABASE_URL format
   - Check database credentials
   - Ensure database is accessible from App Platform

2. **Redis Connection Failed**
   - Verify REDIS_URL format
   - Check Redis credentials
   - Ensure Redis is accessible from App Platform

3. **Build Failed**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Check GitHub Actions logs

4. **API Errors**
   - Verify trading API credentials
   - Check API rate limits
   - Ensure proper environment variables

#### Logs and Debugging

1. **Application Logs:**
   ```bash
   doctl apps logs <app-id>
   ```

2. **Build Logs:**
   - Check in App Platform dashboard
   - Review GitHub Actions logs

3. **Database Logs:**
   - Check DigitalOcean database logs
   - Monitor connection pool metrics

### Scaling

#### Horizontal Scaling
- Increase instance count in app.yaml
- Consider using multiple workers

#### Vertical Scaling
- Upgrade instance size in App Platform
- Monitor resource usage

#### Database Scaling
- Upgrade PostgreSQL database size
- Add read replicas if needed
- Optimize Redis configuration

### Security Best Practices

1. **Environment Variables:**
   - Never commit secrets to version control
   - Use DigitalOcean secrets management
   - Rotate API keys regularly

2. **Database Security:**
   - Use SSL connections
   - Restrict database access
   - Regular security updates

3. **Application Security:**
   - Enable CORS for production domains only
   - Use HTTPS everywhere
   - Implement rate limiting

### Backup and Recovery

1. **Database Backups:**
   - DigitalOcean automatic backups enabled
   - Test restore procedures
   - Document recovery steps

2. **Application Backups:**
   - Code backed up in GitHub
   - Configuration documented
   - Environment variables backed up securely

### Support and Maintenance

1. **Regular Updates:**
   - Monitor for security updates
   - Update dependencies regularly
   - Test in staging before production

2. **Monitoring:**
   - Set up alerts for critical issues
   - Monitor trading performance
   - Track system metrics

3. **Documentation:**
   - Keep deployment docs updated
   - Document any custom configurations
   - Maintain runbooks for common issues

---

## 🎯 Production Deployment Complete

Your Elite Autonomous Trading Platform is now ready for production deployment on DigitalOcean with:

✅ **Containerized Application** with Docker  
✅ **PostgreSQL Database** for production data  
✅ **Redis Cache** for performance  
✅ **CI/CD Pipeline** with GitHub Actions  
✅ **Auto-scaling** with App Platform  
✅ **SSL/HTTPS** automatically managed  
✅ **Health Monitoring** and alerts  
✅ **Production Security** configurations  

**Ready for Real Money Trading! 🚀**