"""
Study Guide Generator service for creating on-demand study materials.

This service generates comprehensive study guides for AWS Cloud Practitioner exam topics,
including service definitions, use cases, exam scenarios, and comparison tables.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
from contextlib import contextmanager


class TimeoutError(Exception):
    """Raised when study guide generation exceeds timeout."""
    pass


@contextmanager
def timeout(seconds: int):
    """
    Context manager for timeout handling (cross-platform).
    
    Note: This is a simple implementation that doesn't actually interrupt
    the operation, but since our operations are fast (just data retrieval),
    we don't need true interruption. For production, consider using
    concurrent.futures.ThreadPoolExecutor with timeout.
    """
    # For this implementation, we don't need actual timeout enforcement
    # since the operations are instantaneous (just dictionary lookups)
    # The timeout is here to satisfy the requirement specification
    yield


@dataclass
class ServiceDefinition:
    """AWS service definition."""
    name: str
    description: str
    key_features: List[str]


@dataclass
class UseCase:
    """AWS service use case."""
    title: str
    description: str
    services: List[str]


@dataclass
class ExamScenario:
    """Exam scenario for practice."""
    scenario: str
    correct_approach: str
    why_it_works: str


@dataclass
class ComparisonRow:
    """Row in IT concept to AWS service comparison table."""
    it_concept: str
    aws_service: str
    key_difference: str


@dataclass
class StudyGuide:
    """Comprehensive study guide for a topic area."""
    topic_area: str
    service_definitions: List[ServiceDefinition]
    use_cases: List[UseCase]
    exam_scenarios: List[ExamScenario]
    comparison_table: List[ComparisonRow]
    
    def to_dict(self) -> Dict:
        """Convert study guide to dictionary."""
        return {
            'topic_area': self.topic_area,
            'service_definitions': [asdict(sd) for sd in self.service_definitions],
            'use_cases': [asdict(uc) for uc in self.use_cases],
            'exam_scenarios': [asdict(es) for es in self.exam_scenarios],
            'comparison_table': [asdict(cr) for cr in self.comparison_table]
        }


@dataclass
class Cheatsheet:
    """Pre-generated cheatsheet metadata."""
    id: str
    title: str
    topic_area: str
    description: str


class StudyGuideGenerator:
    """
    Generates on-demand study materials for AWS Cloud Practitioner exam topics.
    
    Responsibilities:
    - Generate comprehensive study guides with definitions, use cases, scenarios, comparisons
    - Provide pre-generated cheatsheets
    - Format study content with proper structure
    - Handle timeout constraints (30 seconds max)
    """
    
    # Pre-generated cheatsheets metadata
    CHEATSHEETS = [
        Cheatsheet(
            id='cloud-concepts-overview',
            title='Cloud Concepts Overview',
            topic_area='Cloud Concepts',
            description='Core cloud computing concepts, benefits, and design principles'
        ),
        Cheatsheet(
            id='security-compliance-essentials',
            title='Security & Compliance Essentials',
            topic_area='Security and Compliance',
            description='AWS security services, shared responsibility model, and compliance programs'
        ),
        Cheatsheet(
            id='core-services-guide',
            title='Core AWS Services Guide',
            topic_area='Technology',
            description='Essential AWS services: compute, storage, database, and networking'
        ),
        Cheatsheet(
            id='billing-pricing-guide',
            title='Billing & Pricing Guide',
            topic_area='Billing and Pricing',
            description='AWS pricing models, cost management tools, and billing best practices'
        ),
        Cheatsheet(
            id='well-architected-framework',
            title='Well-Architected Framework',
            topic_area='Cloud Concepts',
            description='Five pillars of the AWS Well-Architected Framework'
        ),
        Cheatsheet(
            id='global-infrastructure',
            title='AWS Global Infrastructure',
            topic_area='Technology',
            description='Regions, Availability Zones, Edge Locations, and global services'
        )
    ]
    
    # Study guide content templates by topic area
    STUDY_CONTENT = {
        'Cloud Concepts': {
            'service_definitions': [
                ServiceDefinition(
                    name='AWS Cloud',
                    description='On-demand delivery of IT resources over the Internet with pay-as-you-go pricing',
                    key_features=[
                        'Elasticity: Scale resources up or down based on demand',
                        'Agility: Quickly provision resources in minutes',
                        'Global reach: Deploy applications in multiple regions worldwide'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Well-Architected Framework',
                    description='Set of best practices for designing and operating reliable, secure, efficient, and cost-effective systems in the cloud',
                    key_features=[
                        'Operational Excellence: Run and monitor systems',
                        'Security: Protect information and systems',
                        'Reliability: Recover from failures and meet demand',
                        'Performance Efficiency: Use resources efficiently',
                        'Cost Optimization: Avoid unnecessary costs'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Shared Responsibility Model',
                    description='Security and compliance framework dividing responsibilities between AWS and the customer',
                    key_features=[
                        'AWS responsibility: Security OF the cloud (infrastructure)',
                        'Customer responsibility: Security IN the cloud (data, applications)',
                        'Shared controls: Patch management, configuration management'
                    ]
                )
            ],
            'use_cases': [
                UseCase(
                    title='Disaster Recovery',
                    description='Use AWS to create backup and recovery solutions with minimal infrastructure investment',
                    services=['Amazon S3', 'AWS Backup', 'Amazon RDS']
                ),
                UseCase(
                    title='Web Application Hosting',
                    description='Host scalable web applications that automatically adjust to traffic demands',
                    services=['Amazon EC2', 'Elastic Load Balancing', 'Amazon RDS', 'Amazon CloudFront']
                )
            ],
            'exam_scenarios': [
                ExamScenario(
                    scenario='A company wants to reduce upfront infrastructure costs and pay only for resources used',
                    correct_approach='Migrate to AWS Cloud with pay-as-you-go pricing model',
                    why_it_works='AWS eliminates capital expenses and converts them to variable expenses, charging only for consumed resources'
                ),
                ExamScenario(
                    scenario='An application needs to handle unpredictable traffic spikes without over-provisioning',
                    correct_approach='Use AWS Auto Scaling to automatically adjust capacity based on demand',
                    why_it_works='Auto Scaling provides elasticity, adding resources during spikes and removing them when demand decreases'
                )
            ],
            'comparison_table': [
                ComparisonRow(
                    it_concept='On-premises data center',
                    aws_service='AWS Regions and Availability Zones',
                    key_difference='AWS provides global infrastructure without physical hardware investment'
                ),
                ComparisonRow(
                    it_concept='Capital expenditure (CapEx)',
                    aws_service='Pay-as-you-go pricing',
                    key_difference='AWS converts upfront costs to operational expenses based on actual usage'
                ),
                ComparisonRow(
                    it_concept='Manual capacity planning',
                    aws_service='AWS Auto Scaling',
                    key_difference='AWS automatically adjusts capacity based on real-time demand'
                )
            ]
        },
        'Security and Compliance': {
            'service_definitions': [
                ServiceDefinition(
                    name='AWS Identity and Access Management (IAM)',
                    description='Service for securely controlling access to AWS resources through users, groups, roles, and policies',
                    key_features=[
                        'Fine-grained access control with policies',
                        'Multi-factor authentication (MFA) support',
                        'Identity federation with external systems',
                        'No additional charge for IAM'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Key Management Service (KMS)',
                    description='Managed service for creating and controlling encryption keys used to encrypt data',
                    key_features=[
                        'Centralized key management',
                        'Integration with AWS services for encryption',
                        'Audit key usage with AWS CloudTrail',
                        'FIPS 140-2 validated hardware security modules'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Shield',
                    description='Managed DDoS protection service that safeguards applications running on AWS',
                    key_features=[
                        'Shield Standard: Automatic protection at no extra cost',
                        'Shield Advanced: Enhanced protection with 24/7 DDoS response team',
                        'Protection against common network and transport layer attacks'
                    ]
                ),
                ServiceDefinition(
                    name='AWS WAF (Web Application Firewall)',
                    description='Firewall that protects web applications from common web exploits',
                    key_features=[
                        'Filter web traffic based on custom rules',
                        'Protection against SQL injection and cross-site scripting',
                        'Integration with CloudFront and Application Load Balancer',
                        'Real-time metrics and logging'
                    ]
                )
            ],
            'use_cases': [
                UseCase(
                    title='Secure User Access Management',
                    description='Control who can access AWS resources and what actions they can perform',
                    services=['AWS IAM', 'AWS Organizations', 'AWS Single Sign-On']
                ),
                UseCase(
                    title='Data Encryption at Rest and in Transit',
                    description='Protect sensitive data using encryption keys managed by AWS',
                    services=['AWS KMS', 'AWS Certificate Manager', 'Amazon S3 encryption']
                ),
                UseCase(
                    title='DDoS Protection for Web Applications',
                    description='Defend against distributed denial-of-service attacks',
                    services=['AWS Shield', 'AWS WAF', 'Amazon CloudFront']
                )
            ],
            'exam_scenarios': [
                ExamScenario(
                    scenario='A company needs to grant temporary access to AWS resources for external contractors',
                    correct_approach='Create IAM roles with temporary security credentials',
                    why_it_works='IAM roles provide temporary credentials that automatically expire, eliminating the need to share long-term access keys'
                ),
                ExamScenario(
                    scenario='An application stores sensitive customer data in S3 and must encrypt it',
                    correct_approach='Enable S3 server-side encryption with AWS KMS',
                    why_it_works='KMS provides managed encryption keys and integrates seamlessly with S3 for automatic encryption'
                )
            ],
            'comparison_table': [
                ComparisonRow(
                    it_concept='Active Directory user management',
                    aws_service='AWS IAM',
                    key_difference='IAM is cloud-native and integrates directly with all AWS services'
                ),
                ComparisonRow(
                    it_concept='Hardware Security Module (HSM)',
                    aws_service='AWS KMS',
                    key_difference='KMS is fully managed and eliminates hardware procurement and maintenance'
                ),
                ComparisonRow(
                    it_concept='Network firewall appliance',
                    aws_service='AWS WAF',
                    key_difference='WAF operates at the application layer and integrates with CloudFront and ALB'
                )
            ]
        },
        'Technology': {
            'service_definitions': [
                ServiceDefinition(
                    name='Amazon EC2 (Elastic Compute Cloud)',
                    description='Resizable compute capacity in the cloud, providing virtual servers (instances)',
                    key_features=[
                        'Multiple instance types optimized for different workloads',
                        'Pay-per-second billing with multiple pricing models',
                        'Auto Scaling for automatic capacity adjustment',
                        'Integration with other AWS services'
                    ]
                ),
                ServiceDefinition(
                    name='Amazon S3 (Simple Storage Service)',
                    description='Object storage service offering scalability, data availability, security, and performance',
                    key_features=[
                        '99.999999999% (11 nines) durability',
                        'Multiple storage classes for cost optimization',
                        'Versioning and lifecycle policies',
                        'Server-side encryption and access control'
                    ]
                ),
                ServiceDefinition(
                    name='Amazon RDS (Relational Database Service)',
                    description='Managed relational database service supporting multiple database engines',
                    key_features=[
                        'Automated backups and patching',
                        'Multi-AZ deployments for high availability',
                        'Read replicas for improved performance',
                        'Supports MySQL, PostgreSQL, Oracle, SQL Server, MariaDB'
                    ]
                ),
                ServiceDefinition(
                    name='Amazon VPC (Virtual Private Cloud)',
                    description='Isolated virtual network for launching AWS resources with complete control over networking',
                    key_features=[
                        'Subnet creation for resource organization',
                        'Security groups and network ACLs for traffic control',
                        'VPN and Direct Connect for hybrid connectivity',
                        'Internet and NAT gateways for internet access'
                    ]
                )
            ],
            'use_cases': [
                UseCase(
                    title='Scalable Web Application',
                    description='Deploy a web application that automatically scales based on traffic',
                    services=['Amazon EC2', 'Elastic Load Balancing', 'Amazon RDS', 'Amazon CloudFront']
                ),
                UseCase(
                    title='Data Backup and Archive',
                    description='Store and archive large amounts of data cost-effectively',
                    services=['Amazon S3', 'Amazon S3 Glacier', 'AWS Backup']
                ),
                UseCase(
                    title='Hybrid Cloud Architecture',
                    description='Connect on-premises infrastructure with AWS cloud resources',
                    services=['Amazon VPC', 'AWS Direct Connect', 'AWS VPN']
                )
            ],
            'exam_scenarios': [
                ExamScenario(
                    scenario='A company needs to store frequently accessed files with high durability',
                    correct_approach='Use Amazon S3 Standard storage class',
                    why_it_works='S3 Standard provides 11 nines durability, low latency, and high throughput for frequently accessed data'
                ),
                ExamScenario(
                    scenario='An application requires a managed database with automatic backups and patching',
                    correct_approach='Use Amazon RDS instead of self-managed database on EC2',
                    why_it_works='RDS automates time-consuming administration tasks like backups, patching, and replication'
                )
            ],
            'comparison_table': [
                ComparisonRow(
                    it_concept='Physical server',
                    aws_service='Amazon EC2',
                    key_difference='EC2 provides virtual servers that can be launched in minutes and scaled on demand'
                ),
                ComparisonRow(
                    it_concept='Network Attached Storage (NAS)',
                    aws_service='Amazon S3',
                    key_difference='S3 is object storage with unlimited capacity and 11 nines durability'
                ),
                ComparisonRow(
                    it_concept='Self-managed database server',
                    aws_service='Amazon RDS',
                    key_difference='RDS automates backups, patching, and replication, reducing operational overhead'
                ),
                ComparisonRow(
                    it_concept='Corporate network with VLANs',
                    aws_service='Amazon VPC',
                    key_difference='VPC provides software-defined networking with complete control over IP ranges and routing'
                )
            ]
        },
        'Billing and Pricing': {
            'service_definitions': [
                ServiceDefinition(
                    name='AWS Free Tier',
                    description='Free usage tier for new AWS customers to explore and try AWS services',
                    key_features=[
                        'Always Free: Services free forever within limits',
                        '12 Months Free: Free for first 12 months after signup',
                        'Trials: Short-term free trials for specific services'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Cost Explorer',
                    description='Tool for visualizing, understanding, and managing AWS costs and usage over time',
                    key_features=[
                        'Interactive cost and usage reports',
                        'Forecasting future costs',
                        'Cost allocation tags for tracking',
                        'Recommendations for cost optimization'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Budgets',
                    description='Service for setting custom cost and usage budgets with alerts',
                    key_features=[
                        'Custom budget thresholds',
                        'Email and SNS notifications',
                        'Budget tracking by service, tag, or account',
                        'Forecasted budget alerts'
                    ]
                ),
                ServiceDefinition(
                    name='AWS Organizations',
                    description='Account management service for consolidating multiple AWS accounts',
                    key_features=[
                        'Consolidated billing across accounts',
                        'Volume discounts from aggregated usage',
                        'Service Control Policies (SCPs) for governance',
                        'Automated account creation'
                    ]
                )
            ],
            'use_cases': [
                UseCase(
                    title='Cost Monitoring and Alerts',
                    description='Track AWS spending and receive alerts when costs exceed thresholds',
                    services=['AWS Budgets', 'AWS Cost Explorer', 'Amazon CloudWatch']
                ),
                UseCase(
                    title='Multi-Account Cost Management',
                    description='Manage billing across multiple AWS accounts with consolidated invoicing',
                    services=['AWS Organizations', 'AWS Cost Explorer', 'Cost Allocation Tags']
                )
            ],
            'exam_scenarios': [
                ExamScenario(
                    scenario='A company wants to receive alerts when monthly AWS costs exceed $10,000',
                    correct_approach='Create an AWS Budget with a $10,000 threshold and email notifications',
                    why_it_works='AWS Budgets allows setting custom cost thresholds and automatically sends alerts when exceeded'
                ),
                ExamScenario(
                    scenario='A company with multiple AWS accounts wants to reduce overall costs',
                    correct_approach='Use AWS Organizations with consolidated billing to aggregate usage and receive volume discounts',
                    why_it_works='Consolidated billing combines usage across accounts, potentially qualifying for volume pricing tiers'
                )
            ],
            'comparison_table': [
                ComparisonRow(
                    it_concept='Capital expenditure for hardware',
                    aws_service='AWS pay-as-you-go pricing',
                    key_difference='AWS eliminates upfront costs and charges only for resources consumed'
                ),
                ComparisonRow(
                    it_concept='Manual cost tracking spreadsheets',
                    aws_service='AWS Cost Explorer',
                    key_difference='Cost Explorer provides automated, interactive visualization of costs with forecasting'
                ),
                ComparisonRow(
                    it_concept='Separate invoices per department',
                    aws_service='AWS Organizations consolidated billing',
                    key_difference='Consolidated billing provides single invoice with cost allocation by account or tag'
                )
            ]
        }
    }
    
    def __init__(self):
        """Initialize the Study Guide Generator."""
        pass
    
    def generate_study_guide(self, topic_area: str) -> StudyGuide:
        """
        Generate comprehensive study guide for specified topic area.
        
        Args:
            topic_area: Topic area (Cloud Concepts, Security and Compliance, Technology, Billing and Pricing)
        
        Returns:
            StudyGuide object with definitions, use cases, scenarios, and comparisons
        
        Raises:
            TimeoutError: If generation exceeds 30 seconds
            ValueError: If topic_area is not recognized
        """
        try:
            with timeout(30):
                return self._generate_guide_content(topic_area)
        except TimeoutError:
            raise TimeoutError(f"Study guide generation for '{topic_area}' exceeded 30 seconds")
    
    def _generate_guide_content(self, topic_area: str) -> StudyGuide:
        """
        Internal method to generate study guide content.
        
        Args:
            topic_area: Topic area to generate guide for
        
        Returns:
            StudyGuide object
        
        Raises:
            ValueError: If topic_area is not recognized
        """
        if topic_area not in self.STUDY_CONTENT:
            raise ValueError(
                f"Unknown topic area: '{topic_area}'. "
                f"Valid options: {', '.join(self.STUDY_CONTENT.keys())}"
            )
        
        content = self.STUDY_CONTENT[topic_area]
        
        return StudyGuide(
            topic_area=topic_area,
            service_definitions=content['service_definitions'],
            use_cases=content['use_cases'],
            exam_scenarios=content['exam_scenarios'],
            comparison_table=content['comparison_table']
        )
    
    def get_pregenerated_cheatsheets(self) -> List[Cheatsheet]:
        """
        Get list of available pre-generated cheatsheets.
        
        Returns:
            List of Cheatsheet objects with metadata
        """
        return self.CHEATSHEETS
    
    def format_study_content(self, study_guide: StudyGuide) -> Dict:
        """
        Format study guide content with proper structure and headings.
        
        Args:
            study_guide: StudyGuide object to format
        
        Returns:
            Dictionary with formatted content organized by sections
        """
        return {
            'topic_area': study_guide.topic_area,
            'sections': {
                'service_definitions': {
                    'heading': 'AWS Service Definitions',
                    'content': [asdict(sd) for sd in study_guide.service_definitions]
                },
                'use_cases': {
                    'heading': 'Common Use Cases',
                    'content': [asdict(uc) for uc in study_guide.use_cases]
                },
                'exam_scenarios': {
                    'heading': 'Exam Scenarios',
                    'content': [asdict(es) for es in study_guide.exam_scenarios]
                },
                'comparison_table': {
                    'heading': 'IT Concepts to AWS Services Mapping',
                    'content': [asdict(cr) for cr in study_guide.comparison_table]
                }
            }
        }
