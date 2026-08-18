"""
AWS Certified Security - Specialty Questions
Comprehensive question bank covering all exam domains.
"""
import json
import os

questions = []

# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT RESPONSE (12% of exam)
# ══════════════════════════════════════════════════════════════════════════════

questions += [
    {
        "question_text": "A security team needs to investigate suspicious API calls made to an AWS account. Which combination of services provides the MOST comprehensive forensic capability?",
        "options": [
            "CloudTrail for API logs, CloudWatch Logs Insights for analysis, and S3 for log storage",
            "VPC Flow Logs for network traffic, GuardDuty for threat detection, and Athena for querying",
            "CloudTrail for API logs, Detective for investigation graphs, and CloudTrail Insights for anomalies",
            "Config for resource changes, Systems Manager for remediation, and SNS for notifications"
        ],
        "correct_answer": "CloudTrail for API logs, Detective for investigation graphs, and CloudTrail Insights for anomalies",
        "explanation": "CloudTrail records all API calls providing the audit trail. Detective automatically processes CloudTrail, VPC Flow Logs, and GuardDuty findings into behavior graphs for investigation. CloudTrail Insights identifies unusual API activity. This combination provides the most comprehensive forensic capability for API-related incidents.",
        "memory_technique": "TRAIL leads to DETECTIVE who finds INSIGHTS. CloudTrail logs it, Detective investigates it, Insights spots the unusual.",
        "topic_area": "Incident Response",
        "difficulty_level": 3,
        "it_context_mapping": "Like combining access logs, SIEM correlation, and anomaly detection for security investigations"
    },
    {
        "question_text": "An EC2 instance has been compromised and is making unauthorized outbound connections. What is the FASTEST way to isolate the instance while preserving forensic evidence?",
        "options": [
            "Terminate the instance immediately to stop the attack",
            "Create a snapshot of the EBS volumes, then terminate the instance",
            "Change the security group to deny all inbound and outbound traffic",
            "Stop the instance to preserve state, then create forensic snapshots"
        ],
        "correct_answer": "Change the security group to deny all inbound and outbound traffic",
        "explanation": "Changing the security group to deny all traffic immediately isolates the instance without destroying evidence. The instance remains running (memory intact), all data is preserved, and the isolation is instant. Terminating or stopping destroys memory contents. This is the fastest method that preserves maximum forensic evidence.",
        "memory_technique": "BUILD A WALL. Security groups = instant firewall. Don't destroy (terminate/stop) - isolate (security group).",
        "topic_area": "Incident Response",
        "difficulty_level": 2,
        "it_context_mapping": "Like network segmentation - cutting off all network access without powering down the system"
    },
    {
        "question_text": "A company needs to automate the response to GuardDuty findings indicating compromised credentials. Which solution provides the MOST automated remediation?",
        "options": [
            "GuardDuty sends findings to SNS, which triggers a Lambda function to rotate IAM credentials and revoke active sessions",
            "GuardDuty sends findings to Security Hub, which creates tickets in ServiceNow for manual investigation",
            "GuardDuty sends findings to CloudWatch, which triggers a CloudWatch alarm to notify the security team",
            "GuardDuty sends findings to S3, where they are analyzed daily by a batch processing job"
        ],
        "correct_answer": "GuardDuty sends findings to SNS, which triggers a Lambda function to rotate IAM credentials and revoke active sessions",
        "explanation": "EventBridge (formerly CloudWatch Events) detects GuardDuty findings and triggers Lambda for automated response. The Lambda function can immediately rotate credentials, revoke sessions, isolate resources, and notify teams. This provides real-time automated remediation without human intervention.",
        "memory_technique": "AUTO-PILOT response. GuardDuty FINDS → Lambda ACTS. Real-time automation beats manual tickets or delayed batch.",
        "topic_area": "Incident Response",
        "difficulty_level": 3,
        "it_context_mapping": "Like SOAR (Security Orchestration, Automation, and Response) platforms that automatically respond to security alerts"
    },
    {
        "question_text": "How should a security team preserve CloudTrail logs to meet forensic requirements for long-term investigations?",
        "options": [
            "Keep logs in CloudWatch Logs indefinitely with encryption",
            "Store logs in S3 with versioning, MFA Delete, Object Lock in compliance mode, and cross-region replication",
            "Export logs to Glacier immediately for cost-effective long-term storage",
            "Stream logs to Kinesis Data Firehose for real-time analysis and retention"
        ],
        "correct_answer": "Store logs in S3 with versioning, MFA Delete, Object Lock in compliance mode, and cross-region replication",
        "explanation": "This configuration provides immutable, tamper-proof log storage. Versioning preserves history, MFA Delete prevents unauthorized deletion, Object Lock in compliance mode creates WORM (write-once-read-many) storage that cannot be deleted even by account root, and cross-region replication provides disaster recovery.",
        "memory_technique": "LOCK IT DOWN. Versioning + MFA Delete + Object Lock + Replication = immutable evidence vault.",
        "topic_area": "Incident Response",
        "difficulty_level": 4,
        "it_context_mapping": "Like chain of custody for evidence - ensuring logs cannot be tampered with or deleted"
    },
    {
        "question_text": "What does CloudTrail log file integrity validation provide?",
        "options": [
            "Validates that log files are in the correct JSON format",
            "Validates that all API calls were authorized by IAM policies",
            "Validates that log files have not been modified, deleted, or forged after CloudTrail delivered them",
            "Validates that log files are encrypted with the correct KMS key"
        ],
        "correct_answer": "Validates that log files have not been modified, deleted, or forged after CloudTrail delivered them",
        "explanation": "CloudTrail log file integrity validation uses cryptographic hashing to prove logs have not been tampered with. CloudTrail creates a hash digest for each log file and signs it with a private key. You can validate the hash chain to detect any tampering, making logs admissible as evidence.",
        "memory_technique": "TAMPER-PROOF seal. Hash + signature = proof logs haven't been modified. Chain of custody for AWS logs.",
        "topic_area": "Incident Response",
        "difficulty_level": 3,
        "it_context_mapping": "Like blockchain or digital signatures - cryptographic proof of data integrity"
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING AND MONITORING (20% of exam)
# ══════════════════════════════════════════════════════════════════════════════

questions += [
    {
        "question_text": "A company needs to monitor all API calls across 50 AWS accounts in an organization. What is the MOST efficient approach?",
        "options": [
            "Enable CloudTrail in each account and aggregate logs into a central S3 bucket",
            "Create an organization trail in the management account that logs events for all accounts",
            "Use AWS Config to track API calls and aggregate configuration data centrally",
            "Enable VPC Flow Logs in each account to capture all network-level API traffic"
        ],
        "correct_answer": "Create an organization trail in the management account that logs events for all accounts",
        "explanation": "An organization trail logs all events from all accounts into a single S3 bucket with a single configuration. This eliminates the need to configure CloudTrail in each account and ensures consistent logging across the organization. It's automatically applied to new accounts as they join.",
        "memory_technique": "ONE TRAIL for ALL ACCOUNTS. Organization trail = centralized logging for entire AWS organization.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 2,
        "it_context_mapping": "Like centralized logging in enterprise environments - one collector for all systems"
    },
    {
        "question_text": "VPC Flow Logs show multiple rejected connection attempts from an external IP to a private subnet. What does this indicate?",
        "options": [
            "The security group is blocking the traffic (intended security posture)",
            "The network ACL is blocking the traffic (intended security posture)",
            "Both security groups and network ACLs are properly configured",
            "An attacker is attempting to scan or exploit resources in the subnet"
        ],
        "correct_answer": "An attacker is attempting to scan or exploit resources in the subnet",
        "explanation": "Multiple rejected connections from an external IP suggests scanning or attack attempts. While security groups/NACLs are blocking it correctly, the pattern indicates malicious activity that should be investigated. GuardDuty would likely flag this as reconnaissance activity.",
        "memory_technique": "REJECTED = someone knocking on doors. Multiple rejections = port scan. Working as designed, but indicates threat.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 2,
        "it_context_mapping": "Like firewall logs showing dropped packets - security is working but threat actor is probing"
    },
    {
        "question_text": "What is the difference between AWS Config and CloudTrail?",
        "options": [
            "Config tracks resource configurations over time; CloudTrail tracks API calls and user activity",
            "Config is for security monitoring; CloudTrail is for cost tracking",
            "Config works only in VPCs; CloudTrail works across all AWS services",
            "Config is real-time; CloudTrail has a 15-minute delay"
        ],
        "correct_answer": "Config tracks resource configurations over time; CloudTrail tracks API calls and user activity",
        "explanation": "Config answers 'What is the state of my resources?' by recording configuration changes and evaluating compliance rules. CloudTrail answers 'Who did what and when?' by recording API calls. Config is for configuration management and compliance; CloudTrail is for auditing and security investigation.",
        "memory_technique": "CONFIG = state of resources (WHAT). TRAIL = audit of actions (WHO did WHAT).",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 2,
        "it_context_mapping": "Config is like configuration management database; CloudTrail is like access logs"
    },
    {
        "question_text": "A security team needs to query CloudTrail logs to find all failed login attempts across multiple accounts. What is the MOST cost-effective approach?",
        "options": [
            "Enable CloudWatch Logs for all trails and use CloudWatch Logs Insights",
            "Store CloudTrail logs in S3 and use Amazon Athena to query with SQL",
            "Export CloudTrail logs to Elasticsearch and use Kibana for queries",
            "Use CloudTrail Event History to search across all accounts"
        ],
        "correct_answer": "Store CloudTrail logs in S3 and use Amazon Athena to query with SQL",
        "explanation": "Athena allows SQL queries directly on S3 data with no infrastructure to manage. You pay only for data scanned, making it cost-effective for ad-hoc queries. CloudWatch Logs Insights costs more for large volumes, and CloudTrail Event History only keeps 90 days and doesn't support complex queries.",
        "memory_technique": "ATHENA = SQL on S3. Pay per query, no servers. Perfect for ad-hoc forensic searches.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 3,
        "it_context_mapping": "Like using SQL to query flat files instead of loading into a database"
    },
    {
        "question_text": "GuardDuty has detected an EC2 instance communicating with a known malicious IP address. What should be the FIRST step in the response process?",
        "options": [
            "Immediately terminate the instance to prevent further damage",
            "Isolate the instance by modifying security groups, then investigate",
            "Create an AMI backup of the instance for forensic analysis",
            "Update the NACL to block the malicious IP address"
        ],
        "correct_answer": "Isolate the instance by modifying security groups, then investigate",
        "explanation": "Immediate isolation prevents further damage while preserving evidence. Modifying security groups is instant and reversible. After isolation, you can safely investigate, collect forensics, and determine root cause. Terminating destroys evidence, and updating NACLs doesn't isolate the instance from other resources.",
        "memory_technique": "CONTAIN first, then INVESTIGATE. Isolation = security group modification. Don't destroy evidence.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 2,
        "it_context_mapping": "Like incident response: contain the breach, then investigate - don't destroy evidence"
    },
    {
        "question_text": "What does Amazon Detective provide that GuardDuty does NOT?",
        "options": [
            "Real-time threat detection using machine learning",
            "Automatic remediation of security findings",
            "Visual investigation graphs showing relationships between entities and events",
            "Continuous monitoring of VPC Flow Logs and DNS logs"
        ],
        "correct_answer": "Visual investigation graphs showing relationships between entities and events",
        "explanation": "GuardDuty detects threats but doesn't help investigate them. Detective automatically processes logs from GuardDuty, CloudTrail, and VPC Flow Logs to create behavior graphs showing relationships between users, IP addresses, resources, and events over time. This visualizes the 'story' of an incident for investigation.",
        "memory_technique": "GuardDuty DETECTS. Detective INVESTIGATES. GuardDuty says 'threat here' - Detective says 'here's what happened'.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 3,
        "it_context_mapping": "GuardDuty is like an IDS; Detective is like a SIEM with correlation and visualization"
    },
    {
        "question_text": "A company needs to ensure VPC Flow Logs are enabled for all VPCs across all accounts. How can this be enforced?",
        "options": [
            "Create an AWS Config rule that checks for Flow Logs and marks non-compliant VPCs",
            "Use an SCP in AWS Organizations to prevent VPC creation without Flow Logs",
            "Implement a Lambda function that runs daily to enable Flow Logs on all VPCs",
            "Use CloudFormation StackSets to deploy Flow Logs to all accounts"
        ],
        "correct_answer": "Create an AWS Config rule that checks for Flow Logs and marks non-compliant VPCs",
        "explanation": "AWS Config has a managed rule 'vpc-flow-logs-enabled' that continuously monitors VPCs and flags non-compliant ones. Config can also trigger automatic remediation using Systems Manager Automation documents to enable Flow Logs on non-compliant VPCs. This provides continuous compliance checking.",
        "memory_technique": "CONFIG for compliance. Checks continuously, flags violations, can auto-remediate. Perfect for 'ensure X is always enabled'.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 3,
        "it_context_mapping": "Like compliance scanning tools that continuously check configurations against policies"
    },
    {
        "question_text": "CloudWatch metric filters on CloudTrail logs can detect security events. Which pattern detects root account usage?",
        "options": [
            "{ $.userIdentity.type = 'Root' }",
            "{ $.userIdentity.principalId = 'AIDAI*' }",
            "{ $.errorCode = 'AccessDenied' && $.userIdentity.type = 'Root' }",
            "{ $.eventName = 'ConsoleLogin' && $.userIdentity.type = 'Root' }"
        ],
        "correct_answer": "{ $.eventName = 'ConsoleLogin' && $.userIdentity.type = 'Root' }",
        "explanation": "This filter detects console logins by the root account specifically. The userIdentity.type field equals 'Root' for root account actions, and eventName 'ConsoleLogin' indicates console access. This combination creates an alert for root account console logins, which should be rare and monitored.",
        "memory_technique": "ROOT + LOGIN = RED ALERT. Filter for userIdentity.type=Root AND ConsoleLogin event.",
        "topic_area": "Logging and Monitoring",
        "difficulty_level": 4,
        "it_context_mapping": "Like SIEM correlation rules that detect privileged account usage"
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE SECURITY (26% of exam)
# ══════════════════════════════════════════════════════════════════════════════

questions += [
    {
        "question_text": "A web application is experiencing a volumetric DDoS attack. What AWS services provide protection?",
        "options": [
            "AWS WAF with rate-based rules and Shield Standard for network-layer protection",
            "Shield Advanced with 24/7 DRT support, WAF for application layer, and CloudFront with Shield integration",
            "Network Firewall with IPS signatures and VPC Flow Logs for detection",
            "Security groups with IP allow lists and NACLs with deny rules"
        ],
        "correct_answer": "Shield Advanced with 24/7 DRT support, WAF for application layer, and CloudFront with Shield integration",
        "explanation": "Shield Advanced provides comprehensive DDoS protection including the DDoS Response Team (DRT), cost protection, and advanced detection. WAF blocks application-layer attacks (SQL injection, XSS). CloudFront provides edge protection and absorbs volumetric attacks. This combination covers all DDoS attack layers.",
        "memory_technique": "SHIELD protects, WAF filters, CloudFront absorbs. Three-layer defense: Network (Shield) + Application (WAF) + Edge (CloudFront).",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 3,
        "it_context_mapping": "Like layered DDoS defense: CDN for volumetric, WAF for application layer, managed service for response"
    },
    {
        "question_text": "What is the difference between security groups and network ACLs?",
        "options": [
            "Security groups are stateless; NACLs are stateful",
            "Security groups operate at instance level and are stateful; NACLs operate at subnet level and are stateless",
            "Security groups allow only; NACLs allow and deny",
            "Security groups are for EC2; NACLs are for all resources"
        ],
        "correct_answer": "Security groups operate at instance level and are stateful; NACLs operate at subnet level and are stateless",
        "explanation": "Security groups are stateful (return traffic automatically allowed) and operate at the instance/ENI level. NACLs are stateless (must explicitly allow both inbound and outbound) and operate at the subnet boundary. Security groups support only allow rules; NACLs support both allow and deny rules with numbered priority.",
        "memory_technique": "Security Groups = STATEFUL + INSTANCE + ALLOW only. NACLs = STATELESS + SUBNET + ALLOW/DENY. SG remembers, NACL doesn't.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 2,
        "it_context_mapping": "Security groups are like host firewalls; NACLs are like network firewalls at the subnet boundary"
    },
    {
        "question_text": "A company wants to allow S3 bucket access from VPC instances without internet traffic. What is the MOST secure solution?",
        "options": [
            "Use NAT Gateway to route S3 traffic privately",
            "Create an S3 VPC Gateway Endpoint with an endpoint policy",
            "Use AWS PrivateLink to connect to S3 privately",
            "Enable S3 bucket encryption and restrict access by IP address"
        ],
        "correct_answer": "Create an S3 VPC Gateway Endpoint with an endpoint policy",
        "explanation": "S3 VPC Gateway Endpoints allow instances to access S3 without internet gateway or NAT, keeping traffic on AWS network. Endpoint policies restrict which buckets can be accessed through the endpoint, providing network-level access control. This eliminates internet exposure and reduces data transfer costs.",
        "memory_technique": "S3 and DynamoDB = GATEWAY endpoints. Private connection, no internet, endpoint policy for access control.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 2,
        "it_context_mapping": "Like a direct private connection to a service without routing through the internet"
    },
    {
        "question_text": "An application in VPC A needs to privately access an internal API in VPC B (different account). What provides the MOST secure connectivity?",
        "options": [
            "VPC Peering between VPC A and VPC B",
            "VPN connection between the two VPCs",
            "AWS PrivateLink with an endpoint service in VPC B and an interface endpoint in VPC A",
            "Internet Gateway with IP restrictions on both sides"
        ],
        "correct_answer": "AWS PrivateLink with an endpoint service in VPC B and an interface endpoint in VPC A",
        "explanation": "PrivateLink exposes services privately using ENIs (interface endpoints). VPC B creates an endpoint service backed by NLB; VPC A creates an interface endpoint. Traffic stays on AWS network, doesn't require VPC peering (no overlapping IP concerns), and the service owner controls access. This is the most secure and scalable approach.",
        "memory_technique": "PrivateLink = EXPOSE services privately. No peering, no overlapping IPs, service owner controls access. Most secure cross-VPC/account.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 4,
        "it_context_mapping": "Like service mesh or API gateway for private service-to-service communication"
    },
    {
        "question_text": "AWS WAF is configured on an Application Load Balancer. Which rule action blocks malicious requests but allows you to test the rule first?",
        "options": [
            "Allow action with logging enabled",
            "Block action with override set to Count",
            "Count action to measure impact before changing to Block",
            "Challenge action with CAPTCHA verification"
        ],
        "correct_answer": "Count action to measure impact before changing to Block",
        "explanation": "Count mode processes requests according to the rule logic but doesn't block them - it only increments a counter. This allows you to measure how many requests would be blocked before committing to Block action, preventing false positives that could impact legitimate users.",
        "memory_technique": "COUNT first, BLOCK later. Test rules in Count mode to measure impact without blocking legitimate traffic.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 2,
        "it_context_mapping": "Like running a firewall rule in log-only mode before enforcing it"
    },
    {
        "question_text": "A company requires deep packet inspection for east-west traffic between VPCs. Which service provides this capability?",
        "options": [
            "AWS WAF with cross-VPC rules",
            "VPC Flow Logs with enhanced analysis",
            "AWS Network Firewall deployed in an inspection VPC",
            "Security groups with detailed logging"
        ],
        "correct_answer": "AWS Network Firewall deployed in an inspection VPC",
        "explanation": "AWS Network Firewall provides stateful inspection, IPS/IDS capabilities, and deep packet inspection. Deploy it in a central inspection VPC with Transit Gateway to route all traffic through the firewall. It can inspect east-west traffic between VPCs using Suricata-compatible rules for protocol detection and payload inspection.",
        "memory_technique": "Network Firewall = DEEP inspection. IPS/IDS, payload analysis, Suricata rules. For east-west traffic between VPCs.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 4,
        "it_context_mapping": "Like a next-generation firewall appliance that inspects traffic content, not just headers"
    },
    {
        "question_text": "What is the purpose of AWS WAF managed rule groups?",
        "options": [
            "Rules that are automatically updated by AWS to protect against new threats",
            "Rules managed by your security team through a central console",
            "Rules that manage other rules in a hierarchical structure",
            "Rules that automatically scale based on traffic volume"
        ],
        "correct_answer": "Rules that are automatically updated by AWS to protect against new threats",
        "explanation": "AWS Managed Rules provide pre-configured rule groups maintained by AWS and AWS Marketplace sellers. They're automatically updated when new threats emerge (new CVEs, attack patterns). This gives you continuously updated protection without manual rule maintenance, covering OWASP Top 10, known bad inputs, and more.",
        "memory_technique": "MANAGED = AWS maintains it. Auto-updated for new threats. OWASP Top 10, bad bots, known CVEs - handled.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 2,
        "it_context_mapping": "Like subscribing to threat intelligence feeds that automatically update firewall rules"
    },
    {
        "question_text": "A company wants to prevent EC2 instances from communicating with the internet while allowing access to AWS services. What is the BEST design?",
        "options": [
            "Deploy instances in private subnets with NAT Gateway for outbound internet",
            "Deploy instances in private subnets with VPC endpoints for AWS services and no internet gateway",
            "Use security groups to block all outbound traffic except to AWS IP ranges",
            "Deploy instances in public subnets with security groups restricting outbound to AWS services only"
        ],
        "correct_answer": "Deploy instances in private subnets with VPC endpoints for AWS services and no internet gateway",
        "explanation": "Private subnets without internet gateway ensure no internet connectivity. VPC endpoints (Gateway for S3/DynamoDB, Interface for other services) allow private access to AWS services without internet. This architecture guarantees instances cannot reach the internet while maintaining AWS service access.",
        "memory_technique": "ZERO internet = Private subnet + NO IGW + VPC endpoints. Fortress design for highly sensitive workloads.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 3,
        "it_context_mapping": "Like an air-gapped network that has controlled access to internal services only"
    },
    {
        "question_text": "How does AWS Shield Standard differ from AWS Shield Advanced?",
        "options": [
            "Standard protects network layer only; Advanced protects application layer",
            "Standard is free and automatic for all AWS customers; Advanced costs $3,000/month and provides DRT support, cost protection, and advanced detection",
            "Standard protects web applications; Advanced protects all AWS resources",
            "Standard provides basic protection; Advanced provides WAF integration"
        ],
        "correct_answer": "Standard is free and automatic for all AWS customers; Advanced costs $3,000/month and provides DRT support, cost protection, and advanced detection",
        "explanation": "Shield Standard is automatically enabled for all customers at no cost, protecting against common network/transport layer DDoS attacks. Shield Advanced adds: 24/7 DDoS Response Team, cost protection (no scaling charges during attacks), advanced detection, WAF included, and near real-time attack notifications. It's for business-critical applications.",
        "memory_technique": "Standard = FREE + automatic for everyone. Advanced = $3K/month + DRT + cost protection. Standard for all, Advanced for critical.",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 2,
        "it_context_mapping": "Like free basic security vs. premium managed security service with dedicated support"
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# IDENTITY AND ACCESS MANAGEMENT (20% of exam)
# ══════════════════════════════════════════════════════════════════════════════

questions += [
    {
        "question_text": "A developer needs access to production DynamoDB tables but should not be able to delete them. What is the MOST secure IAM approach?",
        "options": [
            "Grant full DynamoDB access with an explicit Deny for DeleteTable action",
            "Create a custom policy allowing only Read and Write actions on specific tables",
            "Add developer to a group with PowerUser managed policy",
            "Grant AdministratorAccess with MFA requirement for DeleteTable"
        ],
        "correct_answer": "Create a custom policy allowing only Read and Write actions on specific tables",
        "explanation": "Following least privilege principle, grant only the minimum permissions needed. A custom policy specifying allowed actions (GetItem, PutItem, UpdateItem, Query, Scan) on specific table ARNs gives precise access without deletion capabilities. This is more secure than starting with broad access and denying specific actions.",
        "memory_technique": "LEAST PRIVILEGE = allow what's needed, not deny what's not. Grant minimum, specify resources. Start restrictive.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 2,
        "it_context_mapping": "Like role-based access control - grant specific permissions, not full access with exclusions"
    },
    {
        "question_text": "What is the difference between IAM roles and IAM users?",
        "options": [
            "Roles are for people; users are for applications",
            "Roles are assumed temporarily with temporary credentials; users have long-term credentials",
            "Roles cannot be used by external accounts; users can",
            "Roles are regional; users are global"
        ],
        "correct_answer": "Roles are assumed temporarily with temporary credentials; users have long-term credentials",
        "explanation": "IAM users have permanent credentials (access keys, passwords) that don't rotate automatically. IAM roles are assumed temporarily (15min to 12hrs) and provide temporary security credentials via STS. Roles should be used for applications, services, and cross-account access. Users are for people when SSO isn't available.",
        "memory_technique": "USERS = permanent passwords/keys. ROLES = temporary assumption. Use roles for apps, federated users, cross-account.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 2,
        "it_context_mapping": "Users are like passwords; roles are like Kerberos tickets - temporary, automatically expiring"
    },
    {
        "question_text": "A Lambda function needs to access S3 buckets in another AWS account. What is the BEST way to grant this access?",
        "options": [
            "Share IAM user credentials between accounts via Secrets Manager",
            "Create an IAM role in the bucket account with a trust policy allowing the Lambda execution role to assume it",
            "Make the S3 bucket public and use bucket policies for access control",
            "Use AWS Organizations to automatically grant cross-account access"
        ],
        "correct_answer": "Create an IAM role in the bucket account with a trust policy allowing the Lambda execution role to assume it",
        "explanation": "Cross-account access uses role assumption: (1) Bucket account creates a role with S3 permissions and a trust policy allowing Lambda's execution role to assume it. (2) Lambda execution role has permission to AssumeRole. (3) Lambda assumes the role to get temporary credentials. This is the secure, auditable way for cross-account access.",
        "memory_technique": "CROSS-ACCOUNT = role in target, trust from source, assume to access. Two roles, one trust relationship.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 3,
        "it_context_mapping": "Like delegation tokens - source account assumes an identity in the target account"
    },
    {
        "question_text": "What do IAM permission boundaries do?",
        "options": [
            "Set the maximum permissions an IAM entity can have, even if policies grant more",
            "Define the boundary between on-premises and AWS resources",
            "Create boundaries between different AWS accounts in an organization",
            "Set the minimum permissions required for a specific job function"
        ],
        "correct_answer": "Set the maximum permissions an IAM entity can have, even if policies grant more",
        "explanation": "Permission boundaries define the maximum permissions - they act as a guardrail. Even if an identity-based policy grants broader permissions, the permission boundary limits what can actually be done. This is useful for delegating user/role creation without giving away more permissions than intended.",
        "memory_technique": "BOUNDARY = ceiling, not floor. Maximum possible permissions. Guard against privilege escalation in delegated scenarios.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 4,
        "it_context_mapping": "Like SELinux boundaries - even if permissions are granted, boundaries limit what's possible"
    },
    {
        "question_text": "How do Service Control Policies (SCPs) in AWS Organizations differ from IAM policies?",
        "options": [
            "SCPs grant permissions; IAM policies grant and deny permissions",
            "SCPs limit maximum permissions for all principals in an account; IAM policies grant permissions to specific identities",
            "SCPs apply to root user; IAM policies do not",
            "SCPs are for management account only; IAM policies are for member accounts"
        ],
        "correct_answer": "SCPs limit maximum permissions for all principals in an account; IAM policies grant permissions to specific identities",
        "explanation": "SCPs don't grant permissions - they set boundaries. An SCP acts as a filter defining maximum permissions for all principals (including root!) in an account. IAM policies grant actual permissions. Effective permissions = intersection of SCP and IAM policies. SCPs enable central governance across accounts.",
        "memory_technique": "SCP = organization-level filter. Limits EVERYONE (even root) in an account. IAM = grants within those limits.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 3,
        "it_context_mapping": "SCPs are like group policy objects that apply to entire OUs/accounts; IAM is like individual user permissions"
    },
    {
        "question_text": "An organization wants to enforce MFA for all IAM users accessing the AWS console. What is the BEST approach?",
        "options": [
            "Manually enable MFA for each user through IAM console",
            "Create an IAM policy with condition aws:MultiFactorAuthPresent=true and attach to all users",
            "Use an SCP requiring MFA and apply it to all accounts in the organization",
            "Create a Config rule that checks for MFA and marks non-compliant users"
        ],
        "correct_answer": "Create an IAM policy with condition aws:MultiFactorAuthPresent=true and attach to all users",
        "explanation": "An IAM policy with condition key 'aws:MultiFactorAuthPresent' allows actions only when MFA is present. Attach this to all users or groups to enforce MFA requirement. Actions without MFA authentication will be denied. This programmatically enforces MFA rather than relying on manual configuration.",
        "memory_technique": "MFA condition = aws:MultiFactorAuthPresent. Condition denies actions without MFA. Enforce programmatically.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 3,
        "it_context_mapping": "Like conditional access policies that require MFA before granting access"
    },
    {
        "question_text": "What is AWS IAM Access Analyzer used for?",
        "options": [
            "Analyzing IAM policies to find syntax errors",
            "Identifying resources that are shared with external principals outside your organization or account",
            "Analyzing access patterns to recommend policy optimizations",
            "Monitoring failed authentication attempts in CloudTrail"
        ],
        "correct_answer": "Identifying resources that are shared with external principals outside your organization or account",
        "explanation": "IAM Access Analyzer uses automated reasoning to identify resources (S3 buckets, IAM roles, Lambda functions, etc.) that are accessible from outside your account or organization. It continuously monitors for resources that grant public or cross-account access, helping prevent unintended exposure.",
        "memory_technique": "Access Analyzer = EXTERNAL access detector. Finds resources shared outside your zone of trust. Prevents accidental exposure.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 3,
        "it_context_mapping": "Like a scanner that identifies externally accessible resources to prevent data leakage"
    },
    {
        "question_text": "A company is implementing AWS SSO (IAM Identity Center) for multi-account access. What are the benefits over individual IAM users in each account?",
        "options": [
            "SSO is cheaper than IAM users",
            "SSO provides centralized access management, temporary credentials, automatic propagation to new accounts, and audit trails",
            "SSO allows access without MFA requirements",
            "SSO provides higher permission limits than IAM"
        ],
        "correct_answer": "SSO provides centralized access management, temporary credentials, automatic propagation to new accounts, and audit trails",
        "explanation": "AWS SSO eliminates the need for individual IAM users in each account. Users authenticate once and get a portal showing all permitted accounts. Permission sets are centrally managed and automatically deployed. SSO provides temporary credentials (no long-term access keys), integrates with existing identity providers, and provides centralized auditing.",
        "memory_technique": "SSO = one login, many accounts. Central management, temporary creds, no IAM users per account. Modern approach to multi-account.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 2,
        "it_context_mapping": "Like Active Directory with Kerberos - single authentication, access to multiple resources"
    },
    {
        "question_text": "What is the purpose of AWS STS (Security Token Service)?",
        "options": [
            "Stores security tokens for long-term access",
            "Provides temporary, limited-privilege credentials for AWS API requests",
            "Creates secure tunnels for VPN connections",
            "Manages security group tags and metadata"
        ],
        "correct_answer": "Provides temporary, limited-privilege credentials for AWS API requests",
        "explanation": "STS returns temporary security credentials (access key, secret key, session token) that expire after a defined period (15 minutes to 36 hours). These are used when assuming roles, federating users, or granting temporary cross-account access. STS enables secure, auditable temporary access without long-term credentials.",
        "memory_technique": "STS = temporary ticket booth. Get temp creds, use them, they expire. No permanent passwords, better security.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 2,
        "it_context_mapping": "Like OAuth tokens - temporary credentials with limited lifetime and scope"
    },
    {
        "question_text": "An application needs to authenticate users and provide them with temporary AWS credentials to access S3. What is the BEST service for this?",
        "options": [
            "IAM users with access keys",
            "AWS STS with custom authentication logic",
            "Amazon Cognito Identity Pools for credential vending",
            "AWS SSO with SAML integration"
        ],
        "correct_answer": "Amazon Cognito Identity Pools for credential vending",
        "explanation": "Cognito Identity Pools (Federated Identities) provide temporary AWS credentials to end users after they authenticate through Cognito User Pools, social providers, or SAML. The identity pool maps authenticated identities to IAM roles and vends temporary credentials via STS. This is the managed solution for mobile/web apps needing AWS access.",
        "memory_technique": "Cognito Identity Pools = credential vending machine. Authenticate → get temp AWS creds → access S3. For end-user apps.",
        "topic_area": "Identity and Access Management",
        "difficulty_level": 3,
        "it_context_mapping": "Like OAuth2 + AWS credential exchange - user authenticates, gets temporary AWS access"
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# DATA PROTECTION (22% of exam)
# ══════════════════════════════════════════════════════════════════════════════

questions += [
    {
        "question_text": "What is the difference between AWS KMS and AWS CloudHSM?",
        "options": [
            "KMS is for encryption; CloudHSM is for key generation",
            "KMS is a multi-tenant managed service; CloudHSM provides dedicated single-tenant hardware security modules",
            "KMS is cheaper; CloudHSM provides better security",
            "KMS is for symmetric keys; CloudHSM is for asymmetric keys only"
        ],
        "correct_answer": "KMS is a multi-tenant managed service; CloudHSM provides dedicated single-tenant hardware security modules",
        "explanation": "KMS is a managed, multi-tenant service where AWS handles infrastructure (FIPS 140-2 Level 2). CloudHSM provides dedicated HSM hardware that you manage (FIPS 140-2 Level 3). CloudHSM is for regulatory requirements needing single-tenant key storage or custom key management logic. KMS is simpler and sufficient for most use cases.",
        "memory_technique": "KMS = shared service, AWS manages. CloudHSM = your own HSM hardware, you manage. Level 2 vs. Level 3.",
        "topic_area": "Data Protection",
        "difficulty_level": 3,
        "it_context_mapping": "KMS is like managed certificate authority; CloudHSM is like owning your own hardware security module"
    },
    {
        "question_text": "An S3 bucket contains highly sensitive data. What is the MOST secure encryption configuration?",
        "options": [
            "SSE-S3 with AWS-managed keys",
            "SSE-KMS with AWS-managed CMK",
            "SSE-KMS with customer-managed CMK and key policy restrictions",
            "Client-side encryption before uploading to S3"
        ],
        "correct_answer": "SSE-KMS with customer-managed CMK and key policy restrictions",
        "explanation": "Customer-managed CMK provides: fine-grained access control via key policies, automatic key rotation, CloudTrail logging of key usage, and integration with IAM conditions. You control who can use the key and can audit all usage. This provides defense in depth - even with S3 bucket access, data can't be decrypted without key access.",
        "memory_technique": "CUSTOMER CMK = most control. Key policy + IAM + audit trail. Separate access: bucket access ≠ decrypt access.",
        "topic_area": "Data Protection",
        "difficulty_level": 3,
        "it_context_mapping": "Like envelope encryption with separate key management system - data access doesn't imply decryption access"
    },
    {
        "question_text": "A company needs to rotate secrets (database passwords, API keys) automatically. What is the BEST AWS solution?",
        "options": [
            "Store secrets in S3 with versioning and manually rotate them monthly",
            "Use AWS Secrets Manager with automatic rotation enabled",
            "Use Systems Manager Parameter Store with Lambda rotation functions",
            "Store secrets in environment variables and update them via CodePipeline"
        ],
        "correct_answer": "Use AWS Secrets Manager with automatic rotation enabled",
        "explanation": "Secrets Manager provides automatic rotation for RDS, Redshift, and DocumentDB out of the box. For other secrets, you can use Lambda rotation functions. It handles the rotation logic, updates both the secret and the service, and provides versioning with automatic rollback. It's purpose-built for secret management with rotation.",
        "memory_technique": "Secrets Manager = AUTOMATIC rotation. Integrated with RDS/Redshift. Rotates secret AND updates database. Set it and forget it.",
        "topic_area": "Data Protection",
        "difficulty_level": 2,
        "it_context_mapping": "Like a password manager that automatically changes passwords on a schedule and updates all connections"
    },
    {
        "question_text": "What is envelope encryption and why is it used in AWS KMS?",
        "options": [
            "Encrypting data and putting it in an envelope for secure transmission",
            "Encrypting the data encryption key (DEK) with a master key (CMK), while the DEK encrypts actual data",
            "Encrypting multiple files together in a single encrypted archive",
            "Encrypting the outer layer of network packets for secure transmission"
        ],
        "correct_answer": "Encrypting the data encryption key (DEK) with a master key (CMK), while the DEK encrypts actual data",
        "explanation": "Envelope encryption: (1) Generate a DEK to encrypt data locally (2) Send DEK to KMS for encryption with CMK (3) Store encrypted DEK with encrypted data (4) For decryption, send encrypted DEK to KMS, get plaintext DEK, decrypt data. This avoids sending large data to KMS (performance) and provides key hierarchy for cryptographic best practices.",
        "memory_technique": "ENVELOPE = key encrypts key encrypts data. CMK (never leaves KMS) → encrypts DEK → DEK encrypts data. Two-layer protection.",
        "topic_area": "Data Protection",
        "difficulty_level": 4,
        "it_context_mapping": "Like encrypting a file with AES, then encrypting the AES key with RSA - hierarchical encryption"
    },
    {
        "question_text": "S3 Object Lock has two modes: governance and compliance. What is the key difference?",
        "options": [
            "Governance is temporary; compliance is permanent",
            "Governance can be bypassed with special permissions; compliance cannot be overridden by anyone including root",
            "Governance is for development; compliance is for production",
            "Governance allows read access; compliance denies all access"
        ],
        "correct_answer": "Governance can be bypassed with special permissions; compliance cannot be overridden by anyone including root",
        "explanation": "Governance mode: users with s3:BypassGovernanceRetention permission can remove protection. Compliance mode: NO ONE can delete or modify the object until retention expires, not even root account. Compliance mode provides WORM (write-once-read-many) storage for regulatory requirements like SEC 17a-4.",
        "memory_technique": "GOVERNANCE = bypassable with permission. COMPLIANCE = absolute, even root can't override. Governance for ops, Compliance for regulations.",
        "topic_area": "Data Protection",
        "difficulty_level": 3,
        "it_context_mapping": "Governance is like locked file that admins can unlock; Compliance is like immutable storage that nobody can change"
    },
    {
        "question_text": "A company wants to discover and protect PII (Personally Identifiable Information) in S3 buckets. What AWS service is BEST for this?",
        "options": [
            "AWS Inspector for vulnerability assessment",
            "Amazon Macie for automated sensitive data discovery",
            "AWS Config for compliance checking",
            "Amazon GuardDuty for threat detection"
        ],
        "correct_answer": "Amazon Macie for automated sensitive data discovery",
        "explanation": "Macie uses machine learning to automatically discover, classify, and protect sensitive data in S3. It identifies PII (names, addresses, credit cards), credentials, and custom sensitive data patterns. Macie creates findings for sensitive data exposure and integrates with Security Hub and EventBridge for automated response.",
        "memory_technique": "MACIE = PII detective. ML-powered scanning of S3 for sensitive data. Credit cards, SSNs, names - Macie finds them.",
        "topic_area": "Data Protection",
        "difficulty_level": 2,
        "it_context_mapping": "Like DLP (Data Loss Prevention) tools that scan storage for sensitive information"
    },
    {
        "question_text": "What is the purpose of AWS Certificate Manager (ACM)?",
        "options": [
            "Manages employee certifications and training records",
            "Provisions and manages SSL/TLS certificates for AWS services",
            "Certifies compliance with regulatory standards",
            "Manages encryption certificates for KMS keys"
        ],
        "correct_answer": "Provisions and manages SSL/TLS certificates for AWS services",
        "explanation": "ACM provisions, manages, and deploys SSL/TLS certificates for CloudFront, ALB, API Gateway, and other integrated services. It provides free public certificates with automatic renewal, eliminating manual certificate management. ACM Private CA creates certificates for internal resources. Certificates never leave AWS and can't be exported (public certs).",
        "memory_technique": "ACM = SSL/TLS manager. Free certs, auto-renewal, integrated with ALB/CloudFront. No manual certificate hassles.",
        "topic_area": "Data Protection",
        "difficulty_level": 2,
        "it_context_mapping": "Like Let's Encrypt but managed by AWS with automatic deployment to AWS services"
    },
    {
        "question_text": "An RDS database needs encryption at rest. When should encryption be enabled?",
        "options": [
            "Encryption can be enabled on an existing unencrypted RDS instance",
            "Encryption must be enabled at database creation time; cannot be added later",
            "Encryption is automatically enabled for all RDS instances",
            "Encryption can be toggled on and off at any time without downtime"
        ],
        "correct_answer": "Encryption must be enabled at database creation time; cannot be added later",
        "explanation": "RDS encryption at rest must be specified when creating the database. For existing unencrypted databases, you must create an encrypted snapshot, then restore the snapshot to a new encrypted instance. This is a limitation of the underlying storage encryption - it's not a flip-a-switch feature.",
        "memory_technique": "RDS encryption = CREATION TIME only. Can't add later. Migrate via snapshot→restore if needed. Plan ahead.",
        "topic_area": "Data Protection",
        "difficulty_level": 2,
        "it_context_mapping": "Like full-disk encryption that must be set up during installation, can't be added to existing system"
    },
    {
        "question_text": "What are AWS KMS grants used for?",
        "options": [
            "Granting budget increases for KMS usage",
            "Granting temporary, granular permissions to use KMS keys without modifying key policies",
            "Granting users permission to create new KMS keys",
            "Granting automatic key rotation permissions"
        ],
        "correct_answer": "Granting temporary, granular permissions to use KMS keys without modifying key policies",
        "explanation": "Grants provide temporary, programmatic access to KMS keys without modifying key policies. Services like EBS, RDS, and S3 use grants to encrypt/decrypt your data on your behalf. Grants can have constraints (encryption context) and can be revoked. They're useful for delegating access without policy management overhead.",
        "memory_technique": "GRANTS = temporary key permissions. Services use grants to encrypt your data. Don't pollute key policy with temp permissions.",
        "topic_area": "Data Protection",
        "difficulty_level": 4,
        "it_context_mapping": "Like temporary access tokens vs. permanent policy entries - grants are ephemeral delegated permissions"
    },
    {
        "question_text": "A company must ensure that S3 bucket data is never made public under any circumstances. What is the MOST effective control?",
        "options": [
            "Set a bucket policy denying public access",
            "Use S3 Block Public Access at the account level",
            "Configure bucket ACLs to deny public permissions",
            "Use IAM policies to prevent bucket policy modifications"
        ],
        "correct_answer": "Use S3 Block Public Access at the account level",
        "explanation": "S3 Block Public Access at the account level overrides all bucket policies and ACLs that would grant public access. Even if someone creates a public bucket policy, Block Public Access prevents it from taking effect. This provides a centralized, account-wide control that cannot be bypassed by individual bucket configurations.",
        "memory_technique": "BLOCK PUBLIC ACCESS = master override. Account-level protection overrides everything. Insurance policy against accidents.",
        "topic_area": "Data Protection",
        "difficulty_level": 2,
        "it_context_mapping": "Like a master switch that disables a feature system-wide regardless of individual configurations"
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# WRITE OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

output_data = {
    "module": {
        "name": "AWS Certified Security - Specialty",
        "slug": "aws-security-specialty",
        "description": "Prepare for the AWS Certified Security - Specialty (SCS-C02) exam covering incident response, logging, infrastructure security, identity management, and data protection",
        "icon": "security",
        "exam_question_count": 65,
        "exam_time_limit_seconds": 10800,
        "exam_passing_score": 75.0,
        "topic_areas": [
            "Incident Response",
            "Logging and Monitoring",
            "Infrastructure Security",
            "Identity and Access Management",
            "Data Protection"
        ]
    },
    "questions": questions
}

out_path = os.path.join(os.path.dirname(__file__), "scs_module_ready.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

from collections import Counter
topic_counts = Counter(q["topic_area"] for q in questions)
diff_counts = Counter(q["difficulty_level"] for q in questions)

print(f"AWS Security Specialty Module Created!")
print(f"Total questions: {len(questions)}")
print(f"\nBy topic area:")
for topic, count in sorted(topic_counts.items()):
    print(f"  {topic}: {count}")
print(f"\nBy difficulty:")
for level in sorted(diff_counts.keys()):
    print(f"  Level {level}: {diff_counts[level]}")
print(f"\nOutput file: {out_path}")
