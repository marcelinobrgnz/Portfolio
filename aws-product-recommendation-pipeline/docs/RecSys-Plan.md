2.1 Data Pipeline & ETL (Glue, S3, Lambda, Data Quality)

S3 layout (data lake style):

s3://your-bucket/raw/amazon/reviews/ – raw CSV/JSON from Kaggle/SNAP
s3://your-bucket/raw/amazon/products/ – raw product metadata
s3://your-bucket/processed/events/ – cleaned, normalized user–item interactions (Parquet, partitioned by date)
s3://your-bucket/processed/items/ – cleaned product catalog
s3://your-bucket/features/ – feature tables for Feature Store

Glue Crawlers:
Crawler 1: raw/amazon/reviews/ → infers schema for raw_reviews table in Glue Data Catalog
Crawler 2: raw/amazon/products/ → raw_products table

Glue ETL Jobs (PySpark or Scala):
Job A – Build events table:
Input: raw_reviews
Output: events table with columns like
user_id, item_id, event_type (view/rating/purchase), rating, timestamp, platform, country
Writes to s3://.../processed/events/dt=YYYY-MM-DD/ in Parquet.
Job B – Build items table:
Input: raw_products
Output: items table with
item_id, category, price_bucket, brand, title, description_embeddings (optional later)
Writes to s3://.../processed/items/.

Scheduling Glue jobs (daily/hourly):
Glue triggers: schedule Job A + Job B daily at, say, 01:00 UTC.
Optionally: event-based triggers from S3 (new raw dump → ETL job).

AWS Lambda for event-driven bits:
Use 1: Lambda triggered on ObjectCreated in a raw/stream/ prefix to:
Do lightweight validation/enrichment
Push cleaned mini-batches to S3 processed/ or to Kinesis for streaming use cases.
Use 2: Lambda to update real-time signals (e.g., last 10 clicks per user) in DynamoDB/Redis for online features.

Data Quality & Validation:
Schema checks: enforce types, non-null fields for user_id, item_id, timestamp.
Statistical checks:
distribution of ratings (0–5), number of events per day, distinct users/items
detect sudden drops/spikes → alert.
Tools:
Build checks in Glue jobs (PySpark + asserts)
Or use Amazon Deequ library for data quality rules.


3. Model Development on SageMaker (CF, Deep Learning, XGBoost)

Training datasets on S3 (input to SageMaker):
s3://.../training/events/ – sampled or filtered interactions (train/val/test split)
s3://.../training/item_features/
s3://.../training/user_features/
Approach 1 – Collaborative Filtering (matrix factorization / neural CF):
Use implicit feedback (views, clicks, purchases) → convert to interaction weights.
Model options:
MF with user/item embeddings
Neural CF / two-tower architecture (user tower + item tower)
Implement as a custom PyTorch script (train.py) in SageMaker.
Approach 2 – Ranking model with XGBoost:
Construct training rows:
user_id, item_id, user_features..., item_features..., context_features..., label (click / purchase).
Use XGBoost LTR (LambdaRank style) or binary classification for “clicked vs not”.
SageMaker Feature Store:
Online/offline feature groups:
user_features_fg – user-level features (activity counts, recency, segments)
item_features_fg – item-level features (popularity, category, price bucket, embedding indices)
Offline store feeds training; online store feeds inference.
Hyperparameter Tuning (Automatic Model Tuning):
Define ranges: embedding_dim, learning_rate, batch_size, regularization strength, etc.
Use HyperparameterTuner in SageMaker to run parallel training jobs on your S3 data.
Objective: maximize NDCG@K / MAP@K or recall@K on validation set.
Model Versioning & Experiment Tracking:
SageMaker Experiments:
Create experiment → trial for each training run.
Log metrics: loss, recall@K, NDCG@K, hit-rate, training time.
Save models to:
s3://.../models/recommender/v1/, v2/, etc.

4. MLOps & Deployment (Pipelines, A/B Testing, Registry, Auto-Scaling)

SageMaker Pipelines (CI/CD):
Typical pipeline steps:
Data preparation step (Glue job or SageMaker processing job)
Training step (Estimator)
Evaluation step (custom script computing ranking metrics)
Conditional step: if metrics > threshold → register model + deploy
Trigger:
Code commit (CodePipeline/CodeBuild)
New data arrival (scheduled).
Model Registry:
Use SageMaker Model Registry:
Register each approved model with metadata (dataset version, metrics, config).
Transition states: PendingManualApproval → Approved → Deprecated.

Deployment status (current project implementation):
- Trained best XGBoost model (`recsys-sklearn-best` job) and produced `model.tar.gz` in S3.
- Registered as model package `amazon-electronics-recsys-v1` in the Model Registry (Approved).
- Deployed as real-time endpoint `recsys-electronics-endpoint` on `ml.m5.2xlarge` for demo and validation.
- Endpoint is deleted when not in use to avoid cost; it can be recreated from the registered model package at any time.

A/B Testing with Endpoints:
Single endpoint, multiple production variants:
Variant A: existing model, 80% traffic
Variant B: new model, 20% traffic
Compare:
CTR, conversion rate, latency, error rate per variant
Decide to roll forward or roll back.
Auto-Scaling:
Endpoint with autoscaling policy:
min_capacity = 1, max_capacity = N (e.g., 10)
Scale on InvocationsPerInstance or CPUUtilization.
Configure via Application Auto Scaling + CloudWatch alarms.

5. Monitoring & Observability (CloudWatch, Model Monitor, Logs, Dashboards)

CloudWatch Metrics:
Endpoint-level:
Invocations, 4xxError, 5xxError, latency p50/p90/p95/p99
Custom application metrics:
CTR by endpoint/variant
Requests per user segment, etc.
SageMaker Model Monitor:
Set up data quality and data drift monitors:
Baseline: training data distribution (features, label)
Schedule: hourly or daily baseline comparison
Alerts: when drift exceeds thresholds.
CloudWatch Logs:
Capture:
Request/response samples (without PII)
Exception traces
Inference times by stage (feature fetch vs model predict).
Custom Dashboard:
CloudWatch dashboards or Grafana:
Panel for model KPIs: accuracy, NDCG@K, recall@K (offline)
Panel for real-time: CTR by variant, latency metrics, error counts.

6. Production Features (Real-Time, Batch, Caching, API Gateway)

Real-Time Inference API (SageMaker Endpoint):
Request:
user_id, optional context (device, location, time)
Flow:
API Gateway receives request
Lambda:
Fetch user/item features (Feature Store / Redis)
Build feature vector
Call SageMaker endpoint
Return ranked list of item_ids + scores.
Batch Inference:
SageMaker Batch Transform or offline job:
Periodically compute top-N recommendations per user
Store in:
S3 batch_recommendations/
DynamoDB or Redis for quick lookup in UI.
Caching Layer (ElastiCache Redis):
Key: user_id, value: precomputed list of recommended item_ids
TTL: e.g., 1–3 hours
On request:
If cached → serve from Redis
Else → call real-time model, populate cache.
API Gateway + Lambda Routing:
External client → API Gateway → Lambda → SageMaker → Redis
Multiple routes:
/recommendations/realtime
/recommendations/batch
/metrics/user/{user_id} (optional analytics)

7. Business Impact Metrics (How You’ll Measure in This Project)
For public data you can’t measure real money, but you can simulate FAANG-style metrics:

CTR improvement:
Offline proxy: percentage of test interactions where recommended items contain the actual clicked/purchased item.
Revenue per user:
Assign synthetic price to items and compute expected revenue uplift from better ranking.
Latency:
Measure p50/p95 inference latency from API Gateway logs and SageMaker metrics (target \<100ms p95).
System uptime:
Availability of endpoint and API Gateway over time; include in dashboards.

#LATER INCLUSION:

1. Why I said “simple first version”
You just finished building a non-trivial data + ETL stack (Glue + S3 + tables).
The next critical step is to prove the end-to-end pipeline works: data → features → model → artifact, without getting stuck in complex modeling details.
A simple first training dataset (only positives, minimal features) lets you:
Validate the schema, S3 paths, SageMaker config, and training script.
Catch issues (column names, types, performance) early.
Then iterate to more realistic ranking logic (negatives, better labels) once the “plumbing” is verified.
FAANG teams do the same: get a working baseline, then improve.

## GOOD INFORMATION ##

Why have a second model at all?
Think of a real FAANG recommender as multi‑stage, not “one model and done”:
Model 1 (CF / Neural CF / Two‑tower):
Learns user–item embeddings directly from interaction patterns.
Great at:
Finding similar items / users.
Handling very sparse signals.
Doing fast candidate generation (“from millions of items to a few hundred likely ones”).
It captures “people like you also liked…” patterns that tree models on hand‑crafted features can miss.
Model 2 (XGBoost ranking model – what we’re building now):
Takes those candidate items (plus rich features) and re‑ranks them very precisely for the current context.
Great at using:
Price buckets, categories, recency, device, session info, etc.
Optimizes directly for CTR / conversion with clear feature importance and easy tuning.
What difference in predictions does this make?
With only XGBoost (Model 2):
You rely heavily on manually engineered features and whatever candidates you happen to consider.
It may miss some latent similarities (e.g., two items bought together often but with very different explicit features).
With both models:
Model 1 proposes a set of items that are behaviorally similar to what the user likes (good recall, more diverse candidates).
Model 2 then scores those candidates using all the rich features (good precision, business‑aware ranking).
Result: better personalization, better coverage of the catalog, and often higher CTR/Revenue than either model alone.
So the second model isn’t just “another predictor”; it plays a different role in the pipeline (candidate generation vs ranking) and typically improves both quality and robustness of the final recommendations.

#####


2. Because labels are all 1, you’ll eventually want to add negative samples (items a user did not interact with) so XGBoost can learn a real ranking; that’s a modeling step we can design once training is stable.

3. Phase 2 – Better modeling (negatives + second model version)
Once v1 is deployed and stable, then:
Extend the training data:
Add negative samples (items user did not click/buy),
Redefine label as 1 (positive) / 0 (negative).
Switch back to a better ranking metric (e.g. val-auc) for HPO.
Train a new model (v2) with this improved dataset:
New training job,
New HPO run,
Register as recsys-v2 in Model Registry.
Do A/B testing:
Endpoint with two variants: v1 (baseline) vs v2 (negatives), split traffic.
