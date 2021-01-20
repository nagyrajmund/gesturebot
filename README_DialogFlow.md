# Retrieving the credentials
- Go to the setting of the Dialogflow (cogwheel) project: https://dialogflow.cloud.google.com/
- Tab ‘General’: click on the name of ‘ProjectID’
- This will take you to the configuration of the Google Cloud project associated with the Dialogflow agent
- From the left-side menu, click on ‘API & Services’
- Then go to ‘Credentials’
- Either select an existing Service Account or create a new one
- In the service account properties page, select ‘ADD KEY’ -> ‘Create new key’.
- Select ‘JSON’ as the Key type.
# Configuring the Unity component
- Copy the contents of the `.json` file to `Unity/dialogflow_demo/gesturebot_Data/credentials.json`
- Set the project url in `Unity/dialogflow_demo/gesturebot_Data/project_url.txt` to the following:
  ```
  https://dialogflow.googleapis.com/v2beta1/projects/PROJECT_ID/agent/sessions/34563:detectIntent
  ```
  where `PROJECT_ID` is the `project_id` found in the credentials file. 
