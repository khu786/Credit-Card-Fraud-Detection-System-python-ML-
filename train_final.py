
import os, joblib, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

df = pd.read_csv("data/fraud_data.csv")
X = df.drop("fraud", axis=1)
y = df["fraud"]

cat_cols = ["country","device","merchant"]
num_cols = ["amount","time_hour"]

prep = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("num", "passthrough", num_cols)
])

model = Pipeline([
    ("prep", prep),
    ("clf", XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        objective="binary:logistic",
        eval_metric="logloss"
    ))
])

X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)
model.fit(X_train,y_train)
pred=model.predict(X_test)
print("Accuracy:", round(accuracy_score(y_test,pred)*100,2), "%")
os.makedirs("saved_models", exist_ok=True)
joblib.dump(model,"saved_models/fraud_new.pkl")
print("Model saved to saved_models/fraud_new.pkl")
