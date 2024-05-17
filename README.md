# FHIR-Package-Comparison-Tool
A tool to compare elements between different packages

To use this Tool:

- Create a new branch
- Add / delete the relevant packages within the 'packages' folder
- Either click https://github.com/NHSDigital/FHIR-Package-Comparison-Tool/actions/workflows/PackageComparisonTool.yml or
  - Click 'Actions' in the toolbar 
  - Left hand side, under actions, click 'Package Comparison Tool'
- Within the table click the 'Run workflow' button
- Choose your branch and choose a single element to compare
- Click the green 'Run workflow' button. Expect it to take 1 minute to run

- Once completed successfully (green tick) go to the main page https://github.com/NHSDigital/FHIR-Package-Comparison-Tool and choose your branch
- Click Index.html
- Click 'download raw file' in the grey banner
- open file to see comparison tables
- To open in Excel, change the file extension from html to xls. choose 'yes' to '[...]. Do you want to open it anyway?'
