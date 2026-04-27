# backend/pricing/utils.py

def get_plan_features(plan):
    """Return a list of feature strings for a plan"""
    default_features = {
        'free': [
            '60 minutes/month processing',
            '100 MB max file size',
            '10 jobs per month',
            'Basic transcription & translation',
            'SRT subtitle export',
        ],
        'pro': [
            '600 minutes/month processing',
            '500 MB max file size',
            'Unlimited jobs',
            'Full transcription & translation',
            'Audio dubbing (2 voices)',
            'SRT/VTT subtitle export',
            'Priority processing',
            'API access',
        ],
        'business': [
            '3000 minutes/month processing',
            '2 GB max file size',
            'Unlimited jobs',
            'Full transcription & translation',
            'Audio & video dubbing (all voices)',
            'Custom voice cloning',
            'SRT/VTT subtitle export',
            'Priority processing',
            'API access',
            'Team collaboration',
            'Dedicated support',
        ],
    }
    return plan.features if plan.features else default_features.get(plan.tier, [])


def format_price(price):
    """Format price for display"""
    if price == 0:
        return 'Free'
    return f'${price:.2f}'