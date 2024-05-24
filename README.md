# FHIR-Package-Comparison-Tool
This repository is maintained by [Interoperability Team]( https://nhsd-confluence.digital.nhs.uk/pages/viewpage.action?spaceKey=IOPS&title=Interoperability+Standards) Any queries contact us via [email](interoperabilityteam@nhs.net).

A tool to compare FHIR elements between different packages

To use this Tool:

- Create a new branch
- Add the relevant packages within the 'packages' folder
- Singluar profiles that are not in a package can be added to 'extracted_packages' folder 
- Either click https://github.com/NHSDigital/FHIR-Package-Comparison-Tool/actions/workflows/PackageComparisonTool.yml or
  - Click 'Actions' in the toolbar 
  - Left hand side, under actions, click 'Package Comparison Tool'
- Within the table click the 'Run workflow' button
- Choose your branch and type the elements to compare seperated by a `,` (no spaces). By default cardinality, mustSupport and bindings (valueSet & strength) tables will be created
- Click the green 'Run workflow' button. Expect it to take 1 minute to run

- Once completed successfully (green tick) go to the main page https://github.com/NHSDigital/FHIR-Package-Comparison-Tool and choose your branch
- Click the .html files
- Click 'download raw file' in the grey banner
- open file to see comparison tables
- To open in Excel, change the file extension from html to xls. choose 'yes' to '[...]. Do you want to open it anyway?'
