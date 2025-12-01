# This repository was created as part of our NUS Orbital 2025 Project (Apollo 11). 
This application aims to help users make more informed trading decisions through utilising Technical Analysis, while combining it with Market Sentiment Analysis to advice the users on whether they should Buy/Sell/Hold the stock.<br>
We used Random Forest Classifier as our prediction algorithm, and MACD, RSI, BB, OBV for our Technical Analysis module to prevent overcomplication.<br> 
The Frontend of this app is hosted on Vercel, while the Backend of this app is hosted on Heroku.

### Website URL 
https://stoonks-integrated-ui.vercel.app/login

## Instructions/User Manual 

### For More Information, please visit our project documentationL https://docs.google.com/document/d/1qSjFYcvqAI-h3niWUJbFe-zl7Blzw9tLPdVAbDsEoVw/edit?usp=sharing

### Account Signup/Login 
Feel free to link your account to signup/login. An example has been shown on the app. Please DO NOT spam the prediction function as there are rate limits on it. 

### How do I use this app? 
1) Go to the website URL
2) Signup/Login via your Google Account (Dont worry, we do not have access to your password)
3) You will be brought into the General Page. It shows you key indexes such as NASDAQ [Indexes are essentially a 'bunch' of stock grouped together, and would reflect the performance of that group as a whole]
4) On the top right hand corner, there is a 'My Profile' Toggle. Feel free to customise your profile 
5) You could search stock tickers (Ill provide you some: AAPL, NVDA, BRK.A) and interact with the charts. Do note that sometimes it might take some time (<30 seconds in all test cases) to load the Chart, Price and the News. This is normal.
6) Click on the 'Get AI Prediction' to be able to see what the model would recommend you to do with the stock. 


### Frontend is for Vue app (with package.json, src/, etc)
### Backend is for Django app (with manage.py, apps/, etc.)

## Main Structure of the Project 
### Frontend 
Frontend contains all of the .vue files, which is meant for login ui, displays of the UI/UX, API Call etc 

### Backend 
Backend is gna be running on Django (and Heroku for backend) for data and logic, and its meant for the data fetching, sentiment database and the API logic 

### User Experience 
User visits Vercel URL (will be used for frontend), and then the dashboard (powered by vue) will work and calls Heroku (for the backend hosting) for sentiment. Will return data in a JSON file.<br> 

Members: Ooi En Jie, Chan Wen Hui Cheryl<br> 
Special thanks to our mentor, Vaishnav Muralidharan, for patiently guiding us through the entire project. 

