# AWS Security Specialty - Quick Reference Cheat Sheet

## 🔥 High-Frequency Exam Topics

### Incident Response
- **CloudTrail** = API audit trail (enable everywhere, validate logs)
- **GuardDuty** = Threat detection (ML-powered, no agents)
- **Security Hub** = Central dashboard (requires Config)
- **Detective** = Investigation graphs (requires GuardDuty)
- **Systems Manager** = Automation & remediation

💡 **Remember**: Isolate compromised instances with security groups (not terminate!)

### Logging & Monitoring
- **CloudTrail** = WHO did WHAT and WHEN (API calls)
- **VPC Flow Logs** = Network traffic (accepted/rejected)
- **Config** = WHAT is the state (resource configuration)
- **CloudWatch** = Metrics, logs, alarms

💡 **Remember**: CloudTrail Event History = 90 days free

### Infrastructure Security
- **Security Groups** = STATEFUL, instance-level, ALLOW only
- **NACLs** = STATELESS, subnet-level, ALLOW/DENY
- **WAF** = Layer 7 protection, rate limiting, managed rules
- **Shield Standard** = FREE DDoS protection (auto-enabled)
- **Shield Advanced** = $3K/month + DRT + cost protection
- **Network Firewall** = IPS/IDS, Suricata rules, deep packet inspection

💡 **Remember**: Security groups = stateful; NACLs = stateless

### Identity & Access Management
- **Roles** = Temporary credentials (PREFERRED)
- **Users** = Long-term credentials (AVOID for apps)
- **Permission Boundaries** = Maximum possible permissions (guardrail)
- **SCPs** = Limit ALL principals in account (including root!)
- **IAM Access Analyzer** = Finds external access
- **Cognito User Pools** = Authentication
- **Cognito Identity Pools** = Credential vending (temp AWS access)

💡 **Remember**: Effective permissions = IAM policy ∩ SCP ∩ Permission boundary

### Data Protection
- **KMS** = Managed, multi-tenant, FIPS 140-2 Level 2
- **CloudHSM** = Single-tenant, FIPS 140-2 Level 3, you manage
- **Envelope Encryption** = CMK encrypts DEK, DEK encrypts data
- **SSE-S3** = AWS-managed keys
- **SSE-KMS** = KMS-managed keys (more control)
- **SSE-C** = Customer-provided keys
- **Secrets Manager** = Auto-rotation (integrates with RDS)
- **Parameter Store** = Simple key-value (cheaper, no rotation)
- **Macie** = PII discovery in S3
- **S3 Object Lock** = WORM storage
  - Governance mode = Bypassable with permissions
  - Compliance mode = Nobody can delete (even root!)

💡 **Remember**: KMS keys NEVER leave KMS unencrypted

## 🎯 Common Exam Patterns

### Cross-Account Access
1. Target account creates role with S3 permissions
2. Target role has trust policy allowing source account
3. Source account has permission to AssumeRole
4. Source assumes role to access target resources

### Automated Remediation
```
GuardDuty Finding → EventBridge → Lambda → Remediate → SNS Notify
```

### Forensics Best Practices
1. DON'T terminate (destroys evidence)
2. Isolate with security groups (instant + preserves memory)
3. Snapshot EBS volumes (forensic copy)
4. Analyze CloudTrail (API history)
5. Use Detective (behavior graphs)

### Encryption Decision Tree
- Need single-tenant HSM? → CloudHSM
- Need FIPS 140-2 Level 3? → CloudHSM
- Need envelope encryption? → KMS
- Most common use case? → KMS with customer-managed CMK

### VPC Endpoint Types
- **Gateway Endpoints** = S3, DynamoDB (route table entries)
- **Interface Endpoints** = Everything else (ENIs with private IPs)
- **PrivateLink** = Your services to other VPCs

## ⚡ Quick Wins for Exam

### Security Group vs NACL
| Feature | Security Group | NACL |
|---------|---------------|------|
| Level | Instance | Subnet |
| State | Stateful | Stateless |
| Rules | Allow only | Allow + Deny |
| Evaluation | All rules | Number order |

### CloudTrail vs Config vs VPC Flow Logs
| Service | Answers | Scope |
|---------|---------|-------|
| CloudTrail | Who did what when | API calls |
| Config | What's the config | Resources state |
| Flow Logs | What traffic | Network packets |

### IAM Policy Evaluation Logic
1. Explicit DENY (always wins)
2. SCP limits (org-level)
3. Permission boundaries (max permissions)
4. Resource-based policy (allow/deny)
5. Identity-based policy (allow/deny)
6. Implicit DENY (default)

**Remember**: DENY always wins!

### KMS Key Types
- **AWS managed** = Automatic, free, can't view/control
- **Customer managed** = You control, rotate, audit
- **AWS owned** = Service-owned, invisible to you

### Shield Standard vs Advanced
| Feature | Standard | Advanced |
|---------|----------|----------|
| Cost | FREE | $3,000/month |
| Coverage | L3/L4 | L3/L4/L7 |
| DRT Support | No | Yes (24/7) |
| Cost Protection | No | Yes |
| WAF Included | No | Yes |

## 🔐 Security Best Practices (Always Correct Answers)

✅ Enable MFA for root and privileged users
✅ Use IAM roles instead of access keys
✅ Enable CloudTrail in all regions
✅ Enable GuardDuty in all regions
✅ Use encryption at rest and in transit
✅ Implement least privilege
✅ Use S3 Block Public Access at account level
✅ Enable versioning for critical S3 buckets
✅ Use separate accounts for workload isolation
✅ Rotate credentials regularly
✅ Enable VPC Flow Logs
✅ Use Config for compliance monitoring
✅ Centralize logs in Security Hub

## 🚨 Red Flags (Usually Wrong Answers)

❌ Make S3 bucket public
❌ Embed credentials in code
❌ Use root account for daily tasks
❌ Disable CloudTrail for cost savings
❌ Terminate instance during investigation
❌ Store secrets in environment variables
❌ Use single AWS account for everything
❌ Disable security services to improve performance

## 💡 Memory Techniques

**SHIELD** protects, **WAF** filters, **CloudFront** absorbs
**TRAIL** logs, **DETECTIVE** investigates, **INSIGHTS** spots unusual
**CONFIG** = state, **TRAIL** = actions
**GROUPS** are stateful, **ACLs** are stateless
**KMS** = managed, **CloudHSM** = you manage
**GOVERNANCE** = bypassable, **COMPLIANCE** = absolute

## 📝 Common Exam Scenarios

1. **Compromised Instance**
   → Isolate with SG → Snapshot → Investigate → Remediate

2. **Automated Credential Rotation**
   → Secrets Manager with Lambda rotation function

3. **Multi-Account Logging**
   → Organization trail in management account

4. **DDoS Protection**
   → Shield Advanced + WAF + CloudFront + Route 53

5. **Cross-Account Access**
   → IAM role with trust policy + AssumeRole

6. **Sensitive Data Discovery**
   → Amazon Macie scans S3 for PII

7. **Immutable Logs**
   → S3 + Versioning + MFA Delete + Object Lock (Compliance)

8. **Private AWS Service Access**
   → VPC Gateway Endpoint (S3/DynamoDB) or Interface Endpoint

## ⏱️ Exam Tips

- **Read carefully**: "MOST secure", "LEAST cost", "FASTEST"
- **Eliminate wrong answers**: Usually 2 obviously wrong
- **Look for AWS best practices**: Security over convenience
- **Multi-service solutions**: Real scenarios combine services
- **Don't overthink**: First instinct often correct
- **Time management**: 2.77 minutes per question
- **Flag and return**: Skip tough ones, come back later

## 🎓 Final Prep Checklist

- [ ] Know all 19 core security services
- [ ] Understand IAM policy evaluation
- [ ] Practice incident response scenarios
- [ ] Memorize encryption options
- [ ] Understand VPC security layers
- [ ] Know logging service differences
- [ ] Practice cross-account access patterns
- [ ] Review AWS security best practices
- [ ] Take timed practice exams
- [ ] Review incorrect answers thoroughly

---

**Good luck on your AWS Certified Security - Specialty exam!** 🔐🛡️
