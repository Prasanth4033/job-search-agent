"""
Sai Prasanth's master resume data.
All ATS-tailored resumes are built from this canonical profile.
No special characters — only plain hyphens, commas, pipes.
"""

CANDIDATE = {
    "name":    "Sai Prasanth Gudibandla",
    "email":   "gspr4033@gmail.com",
    "phone":   "+1 (636) 431-6758",
    "linkedin": "linkedin.com/in/sai-prasanth-gudibandla",
    "location": "United States (Open to Remote / Hybrid / Relocation)",
    "summary_template": (
        "Senior Data Engineer with 11+ years of experience designing and delivering "
        "large-scale data pipelines, cloud data platforms, and analytics solutions. "
        "Proven expertise in {top_skills}. "
        "Certified GCP Professional Data Engineer. Adept at translating business "
        "requirements into robust, scalable, and cost-optimised data architectures "
        "across AWS, GCP, and Databricks ecosystems."
    ),
    # Skill categories — used for ATS keyword matching and section ordering
    "skills": {
        "Cloud - AWS": [
            "AWS", "Amazon Redshift", "AWS Glue", "Amazon S3", "AWS EMR",
            "Amazon Athena", "AWS Lambda", "Amazon Kinesis", "AWS MWAA",
            "AWS Step Functions", "CloudWatch", "IAM", "VPC",
        ],
        "Cloud - GCP": [
            "GCP", "BigQuery", "Dataflow", "Dataproc", "Google Cloud Storage",
            "Pub/Sub", "Cloud Composer", "Vertex AI", "Looker",
        ],
        "Databricks": [
            "Databricks", "Delta Lake", "Unity Catalog", "Lakehouse Architecture",
            "Bronze Silver Gold", "MLflow",
        ],
        "Snowflake": [
            "Snowflake", "Snowpipe", "Streams", "Tasks",
            "Row-Level Security", "Column-Level Security", "Data Sharing",
        ],
        "Big Data": [
            "Apache Spark", "PySpark", "Hadoop", "HDFS", "YARN",
            "Apache Hive", "MapReduce", "Apache Kafka", "Apache NiFi",
        ],
        "ETL / ELT": [
            "AWS Glue", "SSIS", "Informatica PowerCenter", "dbt", "Apache Airflow",
            "Cloud Composer", "ADF", "Talend",
        ],
        "Programming": [
            "Python", "SQL", "PL/SQL", "Scala", "Shell Scripting", "Bash",
        ],
        "DevOps": [
            "Jenkins", "GitLab CI/CD", "Terraform", "Docker", "Kubernetes",
            "Ansible", "Git",
        ],
        "Databases": [
            "PostgreSQL", "MySQL", "Oracle", "MS SQL Server",
            "DynamoDB", "Cassandra", "MongoDB",
        ],
        "Streaming": [
            "Apache Kafka", "Amazon Kinesis", "Google Pub/Sub", "Apache NiFi",
            "Spark Streaming", "Flink",
        ],
    },
    "experience": [
        {
            "title":   "Senior Data Engineer",
            "company": "Charter Communications",
            "location": "Remote, USA",
            "start":   "August 2025",
            "end":     "Present",
            "bullets": [
                "Architect and maintain multi-cloud data pipelines on AWS (Glue, EMR, Redshift) and GCP (BigQuery, Dataflow) processing 10+ TB daily.",
                "Implement Delta Lake on Databricks with Unity Catalog governance, enabling row-level and column-level security for PII datasets.",
                "Optimise Snowflake Snowpipe ingestion reducing data latency from 15 minutes to under 2 minutes.",
                "Lead migration of legacy SSIS packages to Apache Airflow (MWAA) cutting operational overhead by 40 percent.",
                "Design streaming architecture using Apache Kafka and Spark Streaming for real-time customer event processing.",
            ],
        },
        {
            "title":   "Senior Data Engineer",
            "company": "McKinsey and Company",
            "location": "Remote, USA",
            "start":   "September 2024",
            "end":     "June 2025",
            "bullets": [
                "Built GCP-native data platform using BigQuery, Dataflow, and Cloud Composer for global consulting analytics.",
                "Designed dbt transformation framework on BigQuery reducing model execution time by 35 percent.",
                "Implemented Vertex AI feature store integration with BigQuery ML for predictive analytics pipelines.",
                "Automated Terraform-based infrastructure provisioning for Dataproc clusters reducing setup time by 60 percent.",
                "Mentored junior engineers on PySpark optimisation and Spark tuning best practices.",
            ],
        },
        {
            "title":   "Data Engineer",
            "company": "US News and World Report (via HCL Technologies)",
            "location": "Remote, USA",
            "start":   "July 2022",
            "end":     "August 2024",
            "bullets": [
                "Engineered AWS Glue ETL jobs and Lambda functions for ingesting editorial and ranking data into Redshift.",
                "Designed S3 data lake with partitioning strategy improving Athena query performance by 50 percent.",
                "Implemented Kinesis Data Streams for real-time user behaviour tracking feeding downstream ML models.",
                "Developed PL/SQL stored procedures and SQL query optimisation on Oracle and PostgreSQL databases.",
                "Built CI/CD pipelines using Jenkins and GitLab CI/CD for automated testing and deployment.",
            ],
        },
        {
            "title":   "Data Engineer",
            "company": "Windstream Holdings",
            "location": "Remote, USA",
            "start":   "January 2021",
            "end":     "June 2022",
            "bullets": [
                "Migrated on-premise Hadoop/Hive workloads to AWS EMR and GCP Dataproc reducing infrastructure cost by 30 percent.",
                "Built Snowflake data warehouse with Streams and Tasks for incremental CDC processing.",
                "Developed Python and PySpark ETL pipelines for telecom network and billing data.",
                "Implemented Apache Airflow DAGs for workflow orchestration replacing cron-based scheduling.",
            ],
        },
        {
            "title":   "Data Engineer",
            "company": "TVS Eurogrip",
            "location": "Chennai, India",
            "start":   "August 2019",
            "end":     "December 2020",
            "bullets": [
                "Designed SSIS and Informatica PowerCenter ETL workflows for manufacturing and supply chain data.",
                "Built SQL Server and Oracle database solutions for operational reporting and analytics.",
                "Developed PL/SQL packages and stored procedures for complex business logic.",
            ],
        },
        {
            "title":   "Data Engineer",
            "company": "Emerson Electric",
            "location": "Pune, India",
            "start":   "June 2015",
            "end":     "July 2019",
            "bullets": [
                "Implemented Hadoop HDFS and Hive-based data warehouse for IoT sensor analytics.",
                "Developed MapReduce and PySpark jobs for large-scale industrial data processing.",
                "Built Oracle and MS SQL Server database solutions with complex PL/SQL procedures.",
                "Designed Kafka-based streaming pipeline for real-time equipment monitoring alerts.",
            ],
        },
    ],
    "education": [
        {
            "degree":  "Bachelor of Engineering, Electronics and Communication",
            "school":  "Anna University",
            "year":    "2015",
        }
    ],
    "certifications": [
        "Google Cloud Professional Data Engineer",
        "Google Cloud Associate Cloud Engineer",
    ],
}

# Flat list of all skills for fast matching
ALL_SKILLS_FLAT: list = []
for _cat_skills in CANDIDATE["skills"].values():
    ALL_SKILLS_FLAT.extend(_cat_skills)
# Deduplicate preserving order
_seen: set = set()
ALL_SKILLS_FLAT = [s for s in ALL_SKILLS_FLAT if not (_seen.add(s.lower()) or s.lower() in _seen)]
