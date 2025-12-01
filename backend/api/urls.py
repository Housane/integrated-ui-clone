from django.urls import path
from .views import SentimentAnalysisView, StockPredictionView

urlpatterns = [
    path("sentiment/", SentimentAnalysisView.as_view(), name="sentiment"),
    path("predict/", StockPredictionView.as_view(), name="stock_prediction"),
]