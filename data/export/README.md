# Database Exports

This folder contains the exported SQL files for the Smart Air Quality Monitor project.
These files fulfill the requirement: _"All databases should be hosted on https://iot.cpe.ku.ac.th/pma/, or exported as files."_

## Available Exports

- `collected_data.sql`: An exported dataset containing 3 days of real, collected sensor readings (PM2.5, Temp, Humidity, CO) and external API data. Useful for testing the dashboard and trend analysis features without waiting for new hardware data.

## How to use

To test the dashboard immediately without waiting for new hardware data, you can import this collected dataset into your KU database.

1. Go to **[https://iot.cpe.ku.ac.th/pma/](https://iot.cpe.ku.ac.th/pma/)** and log in with your credentials.
2. Click on the **Import** tab at the top.
3. Click **Choose File** and upload `collected_data.sql` from this folder.
4. Scroll down and click **Go** to import the data.

Once imported, your dashboard will instantly display 3 days of historical data, trend predictions, and comparative analysis.
