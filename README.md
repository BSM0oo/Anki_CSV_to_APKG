### Instructions for Deploying Your Flask App to Google Cloud App Engine

To deploy your Flask application to Google Cloud Platform (GCP) using `gcloud app deploy`, follow these steps. We'll also cover how to specify the version number (since this is your 4th version) and address the issue of the app stopping after a week.

### To deploy a new version 
gcloud app deploy --version v6 --promote  

#### to start a new application you'll want to deploy to a new service
gcloud app deploy app.yaml --service=mynewwebapp --version=v1 --promote
but not a new project

#### to show logs
* **gcloud app logs read**

###  **To list prior versions:**
gcloud app versions list --service=default


#### TO Delete prior version
gcloud app versions delete VERSION_ID --service=default

gcloud app versions delete 20240701t190107 20240708t124047 20240727t120638 20240727t121953 20240801t150850 20240801t151113 20240801t151205 20240801t151846 20240801t151904 20240913t122135 20240913t122902 20240913t123614 20240917t165204 20240918t102042 --service=default --quiet

### TO DEPLOY NEW VERSIONS:
gcloud app deploy --version v6 --promote  (see above)

---

#### **Prerequisites**

1. **Install Google Cloud SDK**: Ensure you have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed on your local machine.

2. **Create a GCP Project**: If you haven't already, create a new project in the [Google Cloud Console](https://console.cloud.google.com/).

3. **Initialize the Cloud SDK**: Run the following command and follow the prompts:

   ```bash
   gcloud init
   ```

4. **Enable App Engine for Your Project**:

   ```bash
   gcloud app create --project=YOUR_PROJECT_ID
   ```

   Replace `YOUR_PROJECT_ID` with your actual project ID.

---

#### **Preparing Your Application for Deployment**

1. **Create an `app.yaml` File**: This file configures your App Engine deployment.

   Create a file named `app.yaml` in your project root directory with the following content:

   ```yaml
   runtime: python39  # Use the appropriate Python version
   entrypoint: gunicorn -b :$PORT app:app

   handlers:
     - url: /.*
       script: auto

   # Optional: Configure automatic scaling
   automatic_scaling:
     min_idle_instances: 1
     max_idle_instances: 2
     max_instances: 4
     cpu_utilization:
       target_utilization: 0.6
   ```

   - **runtime**: Specifies the Python version.
   - **entrypoint**: Command to start your application. Adjust if necessary.
   - **automatic_scaling**: Ensures your app remains available and adjusts resources based on demand.

2. **Specify the Version Number/Name**:

   Since this is your 4th version, you can specify the version in two ways:

   - **In the `app.yaml` File**:

     Add the following line to your `app.yaml`:

     ```yaml
     version: v4
     ```

   - **Using the `gcloud` Command**:

     When deploying, include the `--version` flag:

     ```bash
     gcloud app deploy --version v4
     ```

---

#### **Deploying Your Application**

1. **Authenticate with GCP**:

   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy the Application**:

   Navigate to your project directory and run:

   ```bash
   gcloud app deploy --version v4 --promote
   ```

   - **--version v4**: Sets the version name to `v4`.
   - **--promote**: Routes all traffic to this version upon deployment.

3. **Verify Deployment**:

   After deployment, your app will be accessible at:

   ```
   https://YOUR_PROJECT_ID.ue.r.appspot.com
   ```

---

#### **Addressing the App Stopping Issue**

If your app stops working after a week, here are possible reasons and solutions:

1. **Instance Scaling Down to Zero**:

   - **Cause**: App Engine's automatic scaling may scale instances down to zero if there's no traffic.
   - **Solution**: Ensure at least one instance is always running.

     In your `app.yaml`, adjust the scaling settings:

     ```yaml
     automatic_scaling:
       min_idle_instances: 1
       max_idle_instances: 2
     ```

     **Note**: Keeping instances running may incur costs beyond the free tier.

2. **Free Tier Quota Limits**:

   - **Cause**: Exceeding free tier quotas can cause the app to stop until quotas reset.
   - **Solution**:

     - **Monitor Quotas**: Check your quota usage in the [Google Cloud Console Quotas page](https://console.cloud.google.com/iam-admin/quotas).
     - **Optimize Resources**: Reduce resource consumption if possible.
     - **Upgrade Account**: Consider switching to a paid tier for higher quotas.

3. **Application Errors or Crashes**:

   - **Cause**: Unhandled exceptions or memory leaks can crash your app.
   - **Solution**:

     - **Check Logs**: Use the [Logs Explorer](https://console.cloud.google.com/logs/query) to identify errors.
     - **Handle Exceptions**: Ensure your code properly handles exceptions.
     - **Test Locally**: Run your app locally to identify issues before deployment.

4. **Versioning Conflicts**:

   - **Cause**: Multiple versions might conflict or not receive traffic correctly.
   - **Solution**:

     - **Promote the Latest Version**: Use the `--promote` flag during deployment to direct traffic to the new version.
     - **Cleanup Old Versions**: Delete unused versions to avoid confusion and potential charges.

     ```bash
     gcloud app versions list
     gcloud app versions delete VERSION_ID
     ```

5. **Resource Exhaustion**:

   - **Cause**: The app might be using more resources over time.
   - **Solution**:

     - **Increase Instance Class**: Use a higher instance class in `app.yaml`:

       ```yaml
       instance_class: F2
       ```

     - **Optimize Code**: Profile and optimize your application to use resources efficiently.

---

#### **Best Practices**

- **Regular Monitoring**:

  - Set up alerts for errors and quota limits.
  - Regularly check the [Cloud Monitoring](https://console.cloud.google.com/monitoring) dashboard.

- **Logging**:

  - Implement comprehensive logging to troubleshoot issues quickly.
  - Use structured logging to make log analysis easier.

- **Testing Before Deployment**:

  - Use a staging environment or test your app locally with the App Engine emulator.

  ```bash
  dev_appserver.py app.yaml
  ```

- **Automated Deployments**:

  - Consider using CI/CD pipelines for automated testing and deployment.
  - Tools like Cloud Build or GitHub Actions can streamline this process.

---

#### **Example `app.yaml` with Version and Scaling**

```yaml
runtime: python39
entrypoint: gunicorn -b :$PORT app:app

version: v4

handlers:
  - url: /.*
    script: auto

automatic_scaling:
  min_idle_instances: 1
  max_idle_instances: 2
  max_instances: 4
  cpu_utilization:
    target_utilization: 0.6

# Optional: Set instance class for more resources
instance_class: F2
```

---

#### **Additional Tips**

- **Dependencies**:

  - Ensure all your dependencies are listed in a `requirements.txt` file.
  - Use virtual environments to manage dependencies.

- **Updating the App**:

  - When making updates, increment the version number to keep track.
  - Deploy using:

    ```bash
    gcloud app deploy --version v5 --promote
    ```

- **Cleanup**:

  - Regularly delete old versions to save resources and prevent confusion.

---

#### **Understanding Why the App Stops After a Week**

- **Idle Instance Timeouts**:

  - App Engine may stop your application if it remains idle for an extended period.
  - By setting `min_idle_instances`, you keep at least one instance alive.

- **Quotas Reset Daily**:

  - Free tier quotas reset every 24 hours, but if your app exhausts its quota before the reset, it will stop responding.
  - Monitoring and optimizing your app can prevent this.

---

#### **Monitoring and Alerts**

- **Set Up Alerts**:

  - Use [Cloud Monitoring](https://cloud.google.com/monitoring) to set up alerts for when your app becomes unresponsive or hits quota limits.

- **Use Stackdriver Logging**:

  - Analyze logs for errors and unusual activity.
  - Implement custom metrics if necessary.

---

#### **Final Notes**

- **Costs**:

  - Be aware that adjusting scaling settings to keep instances running may incur costs.
  - Regularly check the [Billing](https://console.cloud.google.com/billing) section to monitor charges.

- **Support**:

  - If issues persist, consult the [App Engine documentation](https://cloud.google.com/appengine/docs) or reach out to the [GCP support community](https://cloud.google.com/support-hub).

---

By following these instructions, you should be able to deploy your Flask app to Google Cloud App Engine, specify the version number, and address the issue of the app stopping after a week. Regular monitoring and proper scaling configurations will help keep your application running smoothly.