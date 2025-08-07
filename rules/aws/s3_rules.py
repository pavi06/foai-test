# rules/aws/s3_rules.py

def get_s3_rules():
    return {
        # Storage class transition days
        "s3_standard_to_ia_days": 30,
        "s3_ia_to_glacier_days": 90,
        "s3_glacier_to_deep_archive_days": 180,
        "s3_expiration_days": 2555,
        
        # Lifecycle policy settings
        "s3_excluded_tags": ["environment=prod"],
        "s3_include_previous_versions": False,
        "s3_include_delete_markers": False,
        
        # Additional S3 preferences
        "s3_min_savings_usd": 1,
        "s3_analyze_versioning": True,
        "s3_analyze_logging": True,
        "s3_analyze_encryption": True,
        
        # Transition rules for lifecycle policies
        "transitions": [
            {"days": 30, "tier": "IA"},
            {"days": 90, "tier": "Glacier"},
            {"days": 180, "tier": "Deep Archive"}
        ]
    }

# maintain backwards compatibility
S3_RULES = get_s3_rules() 