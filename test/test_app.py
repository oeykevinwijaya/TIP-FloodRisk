# import unittest
# from unittest.mock import patch
# from app import predict_flood

# class TestFloodPrediction(unittest.TestCase):
#     def test_high_rainfall_prediction(self):
#         test_data = {
#             'temperature': {'data': [{'value': 30}], 'recordTime': "2024-05-08T14:00:00+08:00"},
#             'humidity': {'data': [{'value': 80}], 'recordTime': "2024-05-08T14:00:00+08:00"},
#             'rainfall': {'data': [{'max': 250}], 'recordTime': "2024-05-08T14:00:00+08:00"}
#         }
#         prediction, probability = predict_flood(test_data, return_prob=True)
#         self.assertTrue(probability > 0.50, f"High rainfall prediction failed. Probability: {probability}")

#     def test_no_rainfall_prediction(self):
#         test_data = {
#             'temperature': {'data': [{'value': 30}], 'recordTime': "2024-05-08T14:00:00+08:00"},
#             'humidity': {'data': [{'value': 80}], 'recordTime': "2024-05-08T14:00:00+08:00"},
#             'rainfall': {'data': [{'max': 0}], 'recordTime': "2024-05-08T14:00:00+08:00"}
#         }
#         prediction, probability = predict_flood(test_data, return_prob=True)
#         self.assertTrue(probability <= 0.50, f"No rainfall prediction failed. Probability: {probability}")

# if __name__ == '__main__':
#     unittest.main()

