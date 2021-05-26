*** Settings ***
Documentation    A resource file with reusable keywords and variables.
Library          SeleniumLibrary

*** Variables ***
${SERVER}    localhost:5000
${BROWSER}   Chrome
${DELAY}     0
${MAIN_URL}  http://${SERVER}/

*** Keywords ***
Open Browser To Main Page
  Open Browser  ${MAIN_URL}  ${BROWSER}
  Maximize Browser Window
  Set Selenium Speed  ${DELAY}
  Main Page Should Load

Main Page Should Load
  Wait Until Element Is Visible  code

Input Code
  [Arguments]  ${code}
  Input Text  code  ${code}

Run Code
  [Arguments]  ${code}
  Input Code  ${code}
  Click Element  run

Has Successful Output
  [Arguments]  ${output}
  Click Link  Output
  Wait Until Element Contains  output  ${output}

Kill Run
  Wait Until Element Contains  run  Kill
  Click Element  run
  Wait Until Element Contains  run  Run

Has Error
  [Arguments]  ${error}
  Click Link  Error Console
  Wait Until Element Contains  errors  ${error}
