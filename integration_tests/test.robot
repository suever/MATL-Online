*** Settings ***
Resource  resource.robot


*** Test Cases ***
Successful Load
  Open Browser To Main Page
  [Teardown]  Close Browser


Successful Run
  Open Browser To Main Page
  Run Code  1 2+
  Has Successful Output  3
  [Teardown]  Close Browser

Cancelled Run
  Open Browser to Main Page
  Run Code  l`T
  Kill Run
  Has Error  Job cancelled
  [Teardown]  Close Browser

