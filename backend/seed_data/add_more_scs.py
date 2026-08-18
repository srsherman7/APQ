"""
Additional AWS Security Specialty questions to expand the question bank
Run this to add more questions to the existing set
"""
import json
import os

# Load existing module
with open("scs_module_ready.json", "r", encoding="utf-8") as f:
    data = json.load(f)

existing_questions = data["questions"]
print(f"Existing questions: {len(existing_questions)}")

# Additional questions
additional_questions = [
    # More Incident Response
    {
        "question_text": "A company's AWS account shows signs of cryptocurrency mining. What steps should be taken FIRST?",
        "options": [
            "Rotate all IAM credentials and access keys immediately",
            "Identify the affected resources using GuardDuty findings, isolate them, then investigate",
            "Terminate all EC2 instances to stop the mining",
            "Enable AWS Config to track resource changes"
        ],
        "correct_answer": "Identify the affected resources using GuardDuty findings, isolate them, then investigate",
        "explanation": "GuardDuty specifically detects cryptocurrency mining with findings like 'CryptoCurrency:EC2/BitcoinTool.B'. First identify which resources are compromised using GuardDuty, isolate them (security groups), then investigate root cause. Rotating all credentials may be premature and terminating all instances destroys evidence.",
        "memory_technique": "FIND → ISOLATE → INVESTIGATE. GuardDuty finds cryptomining, isolate the miners, then figure out how they got in.",
        "topic_area": "Incident Response",
        "difficulty_level": 3,
        "it_context_mapping": "Standard incident response: identify scope, contain threat, investigate root cause, remediate"
    },
    
    # More Infrastructure Security  
    {
        "question_text": "A company needs to share an AMI with another AWS account securely. What is the BEST approach?",
        "options": [
            "Make the AMI public so the other account can access it",
            "Share the AMI with the specific AWS account ID using launch permissions",
            "Copy the AMI to an S3 bucket and grant the other account access",
            "Create a snapshot and share the snapshot publicly"
        ],
        "correct_answer": "Share the AMI with the specific AWS account ID using launch permissions",
        "explanation": "AMIs can be shared with specific AWS accounts using launch permissions without making them public. This provides secure, auditable sharing. The owner retains control and can revoke access at any time. Never make AMIs public unless absolutely necessary as they may contain sensitive configuration.",
        "memory_technique": "SHARE AMI = specific account ID. Never public. Launch permissions control access. Owner maintains control.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 2,
        "it_context_mapping": "Like file sharing with specific users vs. making files public on the internet"
    },
    
    {
        "question_text": "What is the purpose of AWS Network Firewall rule groups?",
        "options": [
            "Groups of EC2 instances that share the same firewall rules",
            "Collections of stateful or stateless rules that can be reused across firewall policies",
            "Groups of security groups that are managed together",
            "Collections of WAF rules for network-layer protection"
        ],
        "correct_answer": "Collections of stateful or stateless rules that can be reused across firewall policies",
        "explanation": "Network Firewall rule groups contain sets of stateful or stateless rules. Stateful rule groups can use domain filtering, IPS signatures (Suricata format), or 5-tuple rules. Stateless rule groups use 5-tuple match criteria. Rule groups are reusable across multiple firewall policies, enabling centralized rule management.",
        "memory_technique": "Rule groups = reusable rule collections. Stateful (IPS, domain lists) or Stateless (5-tuple). Build once, use many times.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 3,
        "it_context_mapping": "Like firewall rule templates that can be applied to multiple firewalls"
    },
    
    # More Identity and Access Management
    {
        "question_text": "A Lambda function needs to access DynamoDB. What is the MOST secure way to provide access?",
        "options": [
            "Store IAM access keys in environment variables",
            "Embed IAM access keys in the function code",
            "Assign an execution role to the Lambda function with DynamoDB permissions",
            "Use AWS Secrets Manager to store credentials and retrieve them at runtime"
        ],
        "correct_answer": "Assign an execution role to the Lambda function with DynamoDB permissions",
        "explanation": "Lambda execution roles use IAM roles with temporary credentials automatically rotated by AWS. The Lambda service assumes the role on your behalf. This eliminates long-term credentials and follows the principle of least privilege. Never embed or store long-term credentials for AWS services.",
        "memory_technique": "Lambda + IAM ROLE = no keys needed. Service assumes role automatically. Temp creds, auto-rotated. Best practice.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 1,
        "it_context_mapping": "Like service accounts with federated authentication - no passwords, just role-based access"
    },
    
    {
        "question_text": "What is the purpose of IAM policy conditions?",
        "options": [
            "Conditions that must be met before the policy is created",
            "Additional constraints that must be true for the policy to grant access",
            "Conditions that determine which IAM service to use",
            "Health check conditions for IAM service availability"
        ],
        "correct_answer": "Additional constraints that must be true for the policy to grant access",
        "explanation": "IAM policy conditions add context-based access control. Common conditions: aws:SourceIp (restrict by IP), aws:MultiFactorAuthPresent (require MFA), aws:RequestedRegion (restrict regions), s3:x-amz-server-side-encryption (require encryption). Conditions make policies dynamic and context-aware.",
        "memory_technique": "CONDITIONS = context checks. IP address, MFA, time, region, encryption. Add 'only if' logic to policies.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 3,
        "it_context_mapping": "Like conditional access policies that consider context (location, device, time) before granting access"
    },
    
    # More Data Protection
    {
        "question_text": "What does KMS key rotation do?",
        "options": [
            "Changes the key ID every year for security",
            "Generates a new cryptographic key material while keeping the same key ID",
            "Moves the key to a different AWS region",
            "Rotates which IAM principals can use the key"
        ],
        "correct_answer": "Generates a new cryptographic key material while keeping the same key ID",
        "explanation": "KMS automatic key rotation (yearly) generates new cryptographic material but keeps the same CMK ID. Old versions are retained for decryption of data encrypted with previous versions. Applications don't need to change - the CMK ID remains constant. This provides cryptographic best practice of key rotation without operational overhead.",
        "memory_technique": "KEY ROTATION = new crypto material, same key ID. Apps don't change. Old versions kept for decryption. Auto annual rotation.",
        "topic_area": "Data Protection",
        "difficulty_level": 3,
        "it_context_mapping": "Like password rotation where the username stays the same but the password changes"
    },
    
    {
        "question_text": "An application needs to encrypt data before storing it in S3. What is the difference between client-side and server-side encryption?",
        "options": [
            "Client-side is faster than server-side encryption",
            "Client-side encrypts data before sending to S3; server-side encrypts data after S3 receives it",
            "Client-side uses symmetric keys; server-side uses asymmetric keys",
            "Client-side is for small files; server-side is for large files"
        ],
        "correct_answer": "Client-side encrypts data before sending to S3; server-side encrypts data after S3 receives it",
        "explanation": "Client-side encryption: you encrypt data before uploading to S3 and manage encryption keys yourself. S3 stores ciphertext only. Server-side encryption: you upload plaintext to S3, and S3 encrypts it before storing. Client-side provides end-to-end encryption and key control; server-side is simpler with AWS managing encryption.",
        "memory_technique": "CLIENT-SIDE = you encrypt before upload. SERVER-SIDE = S3 encrypts after receiving. Client = more control, Server = simpler.",
        "topic_area": "Data Protection",
        "difficulty_level": 2,
        "it_context_mapping": "Client-side is like encrypting email before sending; server-side is like encrypted storage at rest"
    },
    
    # More Logging and Monitoring
    {
        "question_text": "What is the maximum retention period for CloudTrail Event History in the console?",
        "options": [
            "7 days",
            "30 days",
            "90 days",
            "1 year"
        ],
        "correct_answer": "90 days",
        "explanation": "CloudTrail Event History in the console provides 90 days of management events for free without creating a trail. For longer retention, you must create a trail that delivers logs to S3 where you control retention. Event History is for quick lookups; trails are for compliance and long-term forensics.",
        "memory_technique": "Event History = 90 days FREE in console. Want more? Create a trail to S3 with your retention policy.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 1,
        "it_context_mapping": "Like application logs that keep last 90 days in memory but archive to storage for longer retention"
    },
    
    {
        "question_text": "A security team needs to monitor failed SSH attempts to EC2 instances. What is the BEST approach?",
        "options": [
            "Enable CloudTrail to log SSH attempts",
            "Use VPC Flow Logs to capture rejected TCP port 22 connections",
            "Enable CloudWatch agent on instances to collect /var/log/auth.log and create metric filters",
            "Use Security Hub to aggregate SSH attempt data"
        ],
        "correct_answer": "Enable CloudWatch agent on instances to collect /var/log/auth.log and create metric filters",
        "explanation": "SSH authentication happens on the instance OS, not captured by CloudTrail or VPC Flow Logs. The CloudWatch agent can collect system logs (auth.log on Linux) and send them to CloudWatch Logs. Create metric filters to detect failed SSH patterns and trigger alarms. This provides application-level visibility.",
        "memory_technique": "SSH logs = OS logs. CloudWatch agent collects system logs. VPC Flow Logs see connections, not auth attempts. Need agent for app logs.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 3,
        "it_context_mapping": "Like collecting application logs vs. network logs - authentication details are in application logs"
    },
    
    {
        "question_text": "What is AWS Security Hub used for?",
        "options": [
            "Providing security training and certification materials",
            "Aggregating security findings from AWS services and partner tools into a single view",
            "Acting as a web application firewall for API Gateway",
            "Managing security group rules centrally"
        ],
        "correct_answer": "Aggregating security findings from AWS services and partner tools into a single view",
        "explanation": "Security Hub is a centralized security and compliance dashboard. It aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Config, and 50+ partner integrations. It runs automated security checks (CIS AWS Foundations, PCI-DSS), provides findings severity prioritization, and enables automated remediation.",
        "memory_technique": "Security Hub = AGGREGATOR. One dashboard for all security findings. GuardDuty + Config + Macie + partners = unified view.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 2,
        "it_context_mapping": "Like a SIEM dashboard that consolidates alerts from all security tools"
    }
]

# Add to existing questions
data["questions"].extend(additional_questions)
print(f"Added {len(additional_questions)} questions")
print(f"Total questions now: {len(data['questions'])}")

# Write updated file
with open("scs_module_ready.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

from collections import Counter
all_questions = data["questions"]
topic_counts = Counter(q["topic_area"] for q in all_questions)
diff_counts = Counter(q["difficulty_level"] for q in all_questions)

print(f"\nFinal distribution:")
print(f"By topic area:")
for topic, count in sorted(topic_counts.items()):
    print(f"  {topic}: {count}")
print(f"By difficulty:")
for level in sorted(diff_counts.keys()):
    print(f"  Level {level}: {diff_counts[level]}")
