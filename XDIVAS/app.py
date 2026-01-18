from flask import Flask, render_template, jsonify, request, session, redirect, url_for, Response, send_from_directory
from flask_socketio import SocketIO, emit
import json
import requests
from datetime import datetime, timedelta
import asyncio
import websockets
import threading
import time
import random
from collections import defaultdict, deque, Counter
import logging
from bs4 import BeautifulSoup
import re
import cloudscraper
import gzip
import brotli
from io import BytesIO
import os
from urllib.parse import unquote
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ivas_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='threading',
                   ping_timeout=60,
                   ping_interval=25)

# Color themes
COLOR_THEMES = {
    'neon': {
        'primary': '#00ff88',
        'secondary': '#00ccff',
        'accent': '#ff00ff',
        'success': '#00ff88',
        'warning': '#ffff00',
        'danger': '#ff3860',
        'dark': '#0a0a0f',
        'card': '#141420',
        'text': '#ffffff',
        'muted': '#a0a0c0'
    },
    'ocean': {
        'primary': '#00b4d8',
        'secondary': '#0077b6',
        'accent': '#90e0ef',
        'success': '#38b000',
        'warning': '#ff9e00',
        'danger': '#e63946',
        'dark': '#0d1b2a',
        'card': '#1b263b',
        'text': '#e0e1dd',
        'muted': '#778da9'
    },
    'sunset': {
        'primary': '#ff6b35',
        'secondary': '#ffa62e',
        'accent': '#ffd166',
        'success': '#06d6a0',
        'warning': '#ffd166',
        'danger': '#ef476f',
        'dark': '#073b4c',
        'card': '#118ab2',
        'text': '#ffffff',
        'muted': '#83c5be'
    },
    'cyber': {
        'primary': '#00ff9d',
        'secondary': '#00b8ff',
        'accent': '#ff00ff',
        'success': '#00ff9d',
        'warning': '#ffd700',
        'danger': '#ff3860',
        'dark': '#000000',
        'card': '#0a0a12',
        'text': '#ffffff',
        'muted': '#8888aa'
    }
}

# Platform colors
PLATFORM_COLORS = {
    'facebook': '#1877f2',
    'whatsapp': '#25d366',
    'instagram': '#e4405f'
}

# Platform gradient colors
PLATFORM_GRADIENTS = {
    'facebook': 'linear-gradient(135deg, #1877f2 0%, #0d5fbf 100%)',
    'whatsapp': 'linear-gradient(135deg, #25d366 0%, #1da851 100%)',
    'instagram': 'linear-gradient(135deg, #e4405f 0%, #c13584 100%)'
}

# Full country list with codes (kept from previous)
COUNTRIES = {
    'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'BD': 'Bangladesh',
    'BJ': 'Benin', 'CF': 'Central African Republic', 'CI': 'Ivory Coast',
    'EG': 'Egypt', 'ET': 'Ethiopia', 'GY': 'Guyana', 'ID': 'Indonesia',
    'IL': 'Israel', 'KH': 'Cambodia', 'LU': 'Luxembourg', 'LY': 'Libya',
    'MG': 'Madagascar', 'MM': 'Myanmar', 'NG': 'Nigeria', 'NP': 'Nepal',
    'PE': 'Peru', 'PH': 'Philippines', 'PK': 'Pakistan', 'SL': 'Sierra Leone',
    'TG': 'Togo', 'TN': 'Tunisia', 'IN': 'India', 'US': 'United States', 
    'GB': 'United Kingdom', 'CA': 'Canada', 'AU': 'Australia', 'DE': 'Germany', 
    'FR': 'France', 'IT': 'Italy', 'ES': 'Spain', 'BR': 'Brazil', 'RU': 'Russia',
    'CN': 'China', 'JP': 'Japan', 'KR': 'South Korea', 'SA': 'Saudi Arabia',
    'AE': 'United Arab Emirates', 'TR': 'Turkey', 'ZA': 'South Africa',
    'KE': 'Kenya', 'GH': 'Ghana', 'MA': 'Morocco', 'UG': 'Uganda', 'TZ': 'Tanzania',
    'ZM': 'Zambia', 'ZW': 'Zimbabwe', 'MX': 'Mexico', 'AR': 'Argentina',
    'CL': 'Chile', 'CO': 'Colombia', 'VE': 'Venezuela', 'EC': 'Ecuador',
    'UY': 'Uruguay', 'PY': 'Paraguay', 'BO': 'Bolivia', 'CR': 'Costa Rica',
    'PA': 'Panama', 'DO': 'Dominican Republic', 'HT': 'Haiti', 'JM': 'Jamaica',
    'CU': 'Cuba', 'GT': 'Guatemala', 'HN': 'Honduras', 'NI': 'Nicaragua',
    'SV': 'El Salvador', 'BZ': 'Belize', 'BS': 'Bahamas', 'BB': 'Barbados',
    'GD': 'Grenada', 'TT': 'Trinidad and Tobago', 'SR': 'Suriname',
    'GF': 'French Guiana', 'MQ': 'Martinique', 'GP': 'Guadeloupe', 'DM': 'Dominica',
    'LC': 'Saint Lucia', 'VC': 'Saint Vincent', 'AG': 'Antigua and Barbuda',
    'KN': 'Saint Kitts and Nevis', 'MS': 'Montserrat', 'TC': 'Turks and Caicos',
    'VG': 'British Virgin Islands', 'VI': 'U.S. Virgin Islands', 'AW': 'Aruba',
    'CW': 'Curaçao', 'SX': 'Sint Maarten', 'BQ': 'Caribbean Netherlands',
    'KY': 'Cayman Islands', 'BM': 'Bermuda', 'PM': 'Saint Pierre and Miquelon',
    'GL': 'Greenland', 'IS': 'Iceland', 'NO': 'Norway', 'SE': 'Sweden',
    'FI': 'Finland', 'DK': 'Denmark', 'EE': 'Estonia', 'LV': 'Latvia',
    'LT': 'Lithuania', 'BY': 'Belarus', 'UA': 'Ukraine', 'PL': 'Poland',
    'CZ': 'Czech Republic', 'SK': 'Slovakia', 'HU': 'Hungary', 'RO': 'Romania',
    'BG': 'Bulgaria', 'RS': 'Serbia', 'HR': 'Croatia', 'SI': 'Slovenia',
    'BA': 'Bosnia and Herzegovina', 'ME': 'Montenegro', 'MK': 'North Macedonia',
    'GR': 'Greece', 'CY': 'Cyprus', 'MT': 'Malta', 'AD': 'Andorra',
    'MC': 'Monaco', 'SM': 'San Marino', 'VA': 'Vatican City', 'LI': 'Liechtenstein',
    'CH': 'Switzerland', 'AT': 'Austria', 'BE': 'Belgium', 'NL': 'Netherlands',
    'IE': 'Ireland', 'PT': 'Portugal', 'SY': 'Syria', 'LB': 'Lebanon',
    'JO': 'Jordan', 'IQ': 'Iraq', 'IR': 'Iran', 'KW': 'Kuwait', 'BH': 'Bahrain',
    'QA': 'Qatar', 'OM': 'Oman', 'YE': 'Yemen', 'SD': 'Sudan', 'MR': 'Mauritania',
    'SN': 'Senegal', 'GM': 'Gambia', 'GW': 'Guinea-Bissau', 'GN': 'Guinea',
    'LR': 'Liberia', 'CM': 'Cameroon', 'TD': 'Chad', 'CF': 'Central African Republic',
    'CG': 'Congo', 'CD': 'DR Congo', 'RW': 'Rwanda', 'BI': 'Burundi',
    'AO': 'Angola', 'MZ': 'Mozambique', 'MW': 'Malawi', 'BW': 'Botswana',
    'NA': 'Namibia', 'SZ': 'Eswatini', 'LS': 'Lesotho', 'MU': 'Mauritius',
    'RE': 'Réunion', 'SC': 'Seychelles', 'KM': 'Comoros', 'MV': 'Maldives',
    'LK': 'Sri Lanka', 'BT': 'Bhutan', 'TM': 'Turkmenistan', 'UZ': 'Uzbekistan',
    'TJ': 'Tajikistan', 'KG': 'Kyrgyzstan', 'KZ': 'Kazakhstan', 'MN': 'Mongolia',
    'TW': 'Taiwan', 'HK': 'Hong Kong', 'MO': 'Macau', 'KP': 'North Korea',
    'VN': 'Vietnam', 'LA': 'Laos', 'TH': 'Thailand', 'MY': 'Malaysia',
    'SG': 'Singapore', 'BN': 'Brunei', 'TL': 'Timor-Leste', 'PG': 'Papua New Guinea',
    'FJ': 'Fiji', 'SB': 'Solomon Islands', 'VU': 'Vanuatu', 'NC': 'New Caledonia',
    'PF': 'French Polynesia', 'WS': 'Samoa', 'TO': 'Tonga', 'KI': 'Kiribati',
    'MH': 'Marshall Islands', 'FM': 'Micronesia', 'NR': 'Nauru', 'TV': 'Tuvalu',
    'PW': 'Palau', 'CK': 'Cook Islands', 'NU': 'Niue', 'TK': 'Tokelau',
    'WF': 'Wallis and Futuna', 'AS': 'American Samoa', 'GU': 'Guam',
    'MP': 'Northern Mariana Islands', 'PR': 'Puerto Rico'
}

# Load cookies
def load_cookies():
    """Load cookies from cookies.json file"""
    cookies = {}
    try:
        with open('cookies.json', 'r') as f:
            raw_cookies = json.load(f)
            logger.info(f"Loaded cookies from file: {list(raw_cookies.keys())}")
            
            for key, value in raw_cookies.items():
                if key in ['XSRF-TOKEN', 'ivas_sms_session']:
                    if '%' in value:
                        value = unquote(value)
                cookies[key] = value
                
    except FileNotFoundError:
        logger.error("cookies.json file not found!")
        cookies = {
    '_fbp': 'fb.1.1768553685476.5929208535090025',
    '_ga': 'GA1.2.1282339504.1768553686',
    'cf_clearance': '4TUB_D1zBiTvjIbuBNdvsXfqOL8NnVimSWblcFKMSYA-1768697580-1.2.1.1-6w0xf6Z2wy3XhOv7b7j1wkrzWMqXiAQ2UPTnRjT0Tg7rrF.eGhxVlTozjqO5om6FPfT4s5te4v0PzF0pS7b7DVUxlaoDoQ.CUmzGWs6..jKXRL66C.YsdVABkIvpbYB4NJYCKP4ee2NpAuP7OE7DICKnhLQd3uf23J.cJ923fTCMQFFs5YQ4vCS6KthoBX0bL.5cKUiAIMz.gUL_PzZjB1et8PpJ4h9ArjkUjLzWhDM',
    '_gid': 'GA1.2.557442583.1768697998',
    '_gat_gtag_UA_191466370_1': '1',
    'XSRF-TOKEN': 'eyJpdiI6InlKRDRHeCtLSHVCMVBqWW92SURVUEE9PSIsInZhbHVlIjoieHRxWXdCM2ZhNG9MdEJBby9DZlpWS3JCZVcvSC9jUmxCdE5wcHNmZFJ2VXRPTEJXeVVGM2I5K0JGMGlONTMreHRmOFJQQWpNaGdsZmliWE1nSzBlQkFKM2lpQWxwajFwcnFtY2x2K0tPZkZBQ2N5OGppRUJDaE0ySUxEUytXTFIiLCJtYWMiOiI3MmJjYmVhZTIzNzlkZTllNmIzMWYyZjIxNjZlODFkZjUzYjFmYzhhOGNjNmJkNGM4MWQxNjI5ZjIyMTA0M2EyIiwidGFnIjoiIn0%3D',
    'ivas_sms_session': 'eyJpdiI6IitVQ1BuNjdKQVZKeVh3b0taQm9UY1E9PSIsInZhbHVlIjoiZ0I0bDhVaE45cE05d3JQM09tc1owVzQ1alVzSFJqaG1JZjFxUW41K0MycHc1Z3hzMlpqWmRyVCtLR1NZa3lhMkV5NWw3MlBaSVJqL1BhZWN5eVByTU1Ca1BJSHFOR1FmK3RUTW11clcxUkVZQVkrMTNkQnRnckhTbCt4TkJDTTQiLCJtYWMiOiI4NGZjOTQyNmU3NzA1ZTFmYjllYTljYzg3MGY3MTQyYzc4Njg1NjZhZWM5NjhiYTBlZmY3OTE1Y2U0ZTc3MTdkIiwidGFnIjoiIn0%3D',
}
    except Exception as e:
        logger.error(f"Error loading cookies: {e}")
        cookies = {}
    
    return cookies

# Initialize cookies
COOKIES = load_cookies()

# Enhanced data storage with themes
class EnhancedDataStorage:
    def __init__(self, max_sms=2000, max_history=200):
        self.live_sms_data = deque(maxlen=max_sms)
        self.platform_counts = Counter({'facebook': 0, 'whatsapp': 0, 'instagram': 0})
        self.country_counts = Counter()
        self.range_counts = Counter()
        self.hourly_stats = defaultdict(lambda: Counter({'facebook': 0, 'whatsapp': 0, 'instagram': 0}))
        self.sid_tracker = set()
        self.last_update_time = None
        self.connection_status = False
        self.history = deque(maxlen=max_history)
        self.analytics = {
            'peak_hours': [],
            'trending_countries': [],
            'sms_rate': 0,
            'avg_response_time': 0
        }
        self.theme = 'neon'  # Default theme
        
    def add_sms(self, sms_data):
        """Add SMS to storage"""
        sid = sms_data.get('sid', '')
        
        if sid in self.sid_tracker:
            return False
            
        self.live_sms_data.appendleft(sms_data)
        self.sid_tracker.add(sid)
        
        platform = sms_data.get('platform', 'unknown')
        country = sms_data.get('country', 'Unknown')
        
        self.platform_counts[platform] += 1
        self.country_counts[country] += 1
        
        hour = datetime.now().strftime("%H:00")
        self.hourly_stats[hour][platform] += 1
        
        # Update analytics
        self._update_analytics()
        
        self.history.append({
            'time': datetime.now().isoformat(),
            'action': 'new_sms',
            'data': sms_data
        })
        
        self.last_update_time = datetime.now()
        return True
        
    def _update_analytics(self):
        """Update analytics data"""
        # Calculate peak hours
        hourly_data = self.hourly_stats
        if hourly_data:
            peak_hours = sorted(
                [(h, sum(stats.values())) for h, stats in hourly_data.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            self.analytics['peak_hours'] = peak_hours
            
        # Trending countries
        if self.country_counts:
            trending = self.country_counts.most_common(5)
            self.analytics['trending_countries'] = trending
            
        # SMS rate (last hour)
        if self.last_update_time:
            hour_ago = datetime.now() - timedelta(hours=1)
            recent_sms = [sms for sms in self.live_sms_data 
                         if datetime.fromisoformat(sms['timestamp']) > hour_ago]
            self.analytics['sms_rate'] = len(recent_sms) / 60  # per minute
        
    def get_top_countries(self, limit=10):
        """Get top countries"""
        return dict(self.country_counts.most_common(limit))
        
    def get_hourly_stats(self, hours=6):
        """Get hourly statistics"""
        hours_list = sorted(self.hourly_stats.keys(), reverse=True)[:hours]
        stats = []
        for hour in hours_list:
            stats.append({
                'hour': hour,
                'facebook': self.hourly_stats[hour]['facebook'],
                'whatsapp': self.hourly_stats[hour]['whatsapp'],
                'instagram': self.hourly_stats[hour]['instagram']
            })
        return stats
        
    def get_platform_percentages(self):
        """Get platform percentages"""
        total = sum(self.platform_counts.values())
        if total == 0:
            return {}
        return {
            platform: (count / total * 100)
            for platform, count in self.platform_counts.items()
        }
        
    def clear(self):
        """Clear all data"""
        self.live_sms_data.clear()
        self.platform_counts.clear()
        self.country_counts.clear()
        self.range_counts.clear()
        self.hourly_stats.clear()
        self.sid_tracker.clear()
        self.history.clear()
        
    def set_theme(self, theme):
        """Set color theme"""
        if theme in COLOR_THEMES:
            self.theme = theme
            return True
        return False

# Initialize data storage
data_storage = EnhancedDataStorage()

class IVASRealTimeScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.base_url = "https://www.ivasms.com"
        self.logged_in = False
        self.csrf_token = None
        self.session_id = None
        self.last_successful_fetch = None
        self.fetch_interval = 30
        self.max_retries = 3
        self.retry_delay = 5
        self.active = False
        self.fetch_count = 0
        
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        self.set_cookies()
        
    def set_cookies(self):
        """Set cookies for the scraper"""
        try:
            for name, value in COOKIES.items():
                self.scraper.cookies.set(name, value, domain='.ivasms.com')
            logger.info("Cookies set successfully")
        except Exception as e:
            logger.error(f"Error setting cookies: {e}")
            
    def decompress_response(self, response):
        """Decompress response content if encoded"""
        encoding = response.headers.get('Content-Encoding', '').lower()
        content = response.content
        
        try:
            if encoding == 'gzip':
                content = gzip.decompress(content)
            elif encoding == 'br':
                content = brotli.decompress(content)
            return content.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Error decompressing response: {e}")
            return response.text
            
    def login_with_cookies(self):
        """Login to IVAS using cookies"""
        try:
            logger.info("Attempting to login with cookies...")
            
            response = self.scraper.get(f"{self.base_url}/portal", timeout=10)
            
            if response.status_code == 200:
                html_content = self.decompress_response(response)
                
                if 'logout' in html_content.lower() or 'Riyad Mahfuz' in html_content:
                    logger.info("Already logged in with cookies")
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    csrf_input = soup.find('input', {'name': '_token'})
                    if csrf_input:
                        self.csrf_token = csrf_input.get('value')
                        
                    session_input = soup.find('input', {'name': '_session'})
                    if session_input:
                        self.session_id = session_input.get('value')
                        
                    self.logged_in = True
                    data_storage.connection_status = True
                    return True
                    
            logger.info("Explicit login attempt...")
            response = self.scraper.get(f"{self.base_url}/login", timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(self.decompress_response(response), 'html.parser')
                csrf_input = soup.find('input', {'name': '_token'})
                
                if csrf_input:
                    self.csrf_token = csrf_input.get('value')
                    
                    portal_response = self.scraper.get(f"{self.base_url}/portal", timeout=10)
                    if portal_response.status_code == 200:
                        self.logged_in = True
                        data_storage.connection_status = True
                        logger.info("Login successful")
                        return True
                        
        except Exception as e:
            logger.error(f"Login error: {e}")
            
        self.logged_in = False
        data_storage.connection_status = False
        return False
        
    def fetch_live_test_sms(self):
        """Fetch live test SMS from IVAS portal"""
        if not self.logged_in:
            logger.warning("Not logged in, attempting to login...")
            if not self.login_with_cookies():
                logger.error("Login failed, cannot fetch SMS")
                return []
                
        try:
            logger.info(f"Fetch #{self.fetch_count + 1}: Live test SMS from IVAS...")
            
            response = self.scraper.get(
                f"{self.base_url}/portal/live/test_sms",
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch SMS page: {response.status_code}")
                return []
                
            html_content = self.decompress_response(response)
            soup = BeautifulSoup(html_content, 'html.parser')
            sms_table = soup.find('table', {'id': 'LiveTestSMS'})
            sms_list = []
            
            if sms_table:
                rows = sms_table.find_all('tr')
                logger.info(f"Found {len(rows)} rows in SMS table")
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        first_col = cols[0].get_text(strip=True)
                        sid = cols[1].get_text(strip=True) if len(cols) > 1 else "N/A"
                        message = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        
                        country_match = re.search(r'([A-Z]{2})', first_col)
                        country_code = country_match.group(1) if country_match else 'US'
                        country = COUNTRIES.get(country_code, 'Unknown')
                        
                        phone_match = re.search(r'(\+\d{1,3}[\s\d\-\(\)]+|\d{10,})', first_col)
                        phone_number = phone_match.group(1) if phone_match else ""
                        
                        if phone_number:
                            phone_number = re.sub(r'\s+', '', phone_number)
                        
                        platform = self.detect_platform(sid, message, first_col)
                        
                        if platform in ['facebook', 'whatsapp', 'instagram']:
                            sms_data = {
                                'platform': platform,
                                'country': country,
                                'country_code': country_code,
                                'sid': sid,
                                'phone_number': phone_number,
                                'message': message,
                                'time': datetime.now().strftime("%H:%M:%S"),
                                'timestamp': datetime.now().isoformat(),
                                'raw_text': first_col,
                                'id': hashlib.md5(f"{sid}{message}{datetime.now().timestamp()}".encode()).hexdigest()[:8]
                            }
                            sms_list.append(sms_data)
                            
                logger.info(f"Successfully parsed {len(sms_list)} SMS records")
                
            self.fetch_top_ranges(soup)
            self.last_successful_fetch = datetime.now()
            self.fetch_count += 1
            
            return sms_list
            
        except Exception as e:
            logger.error(f"Error fetching SMS: {e}")
            return []
            
    def fetch_top_ranges(self, soup=None):
        """Fetch top ranges from the page"""
        try:
            if not soup:
                response = self.scraper.get(f"{self.base_url}/portal/live/test_sms", timeout=10)
                soup = BeautifulSoup(self.decompress_response(response), 'html.parser')
                
            range_section = soup.find('div', {'class': 'card-body'})
            if range_section:
                ranges = []
                range_elements = range_section.find_all(['div', 'span', 'p'])
                
                for element in range_elements:
                    text = element.get_text(strip=True)
                    if re.search(r'\+\d+|range|number', text.lower()):
                        ranges.append(text)
                        
                if ranges:
                    logger.info(f"Found {len(ranges)} ranges")
                    for range_text in ranges:
                        data_storage.range_counts[range_text] += 1
                        
        except Exception as e:
            logger.error(f"Error fetching ranges: {e}")
            
    def detect_platform(self, sid, message, raw_text=""):
        """Detect platform from SMS data"""
        combined_text = (sid + " " + message + " " + raw_text).lower()
        
        facebook_patterns = [
            r'facebook', r'fb\.com', r'fb\.me', r'meta', r'face',
            r'verify facebook', r'facebook code', r'fb code',
            r'facebook login', r'fb login'
        ]
        
        whatsapp_patterns = [
            r'whatsapp', r'wa\.me', r'whats app', r'whats',
            r'verify whatsapp', r'whatsapp code', r'wa code',
            r'whatsapp login'
        ]
        
        instagram_patterns = [
            r'instagram', r'ig', r'insta',
            r'verify instagram', r'instagram code', r'ig code',
            r'instagram login'
        ]
        
        for pattern in facebook_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return 'facebook'
                
        for pattern in whatsapp_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return 'whatsapp'
                
        for pattern in instagram_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return 'instagram'
                
        return 'facebook'
        
    def start_monitoring(self):
        """Start monitoring IVAS for real-time updates"""
        self.active = True
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Started IVAS monitoring with enhanced animations")
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.active = False
        logger.info("Stopped IVAS monitoring")
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        retry_count = 0
        
        while self.active:
            try:
                if not self.logged_in:
                    self.login_with_cookies()
                    
                if self.logged_in:
                    new_sms = self.fetch_live_test_sms()
                    
                    if new_sms:
                        processed_count = 0
                        animation_data = {
                            'facebook': 0,
                            'whatsapp': 0,
                            'instagram': 0
                        }
                        
                        for sms in new_sms:
                            if data_storage.add_sms(sms):
                                processed_count += 1
                                animation_data[sms['platform']] += 1
                                
                                # Enhanced socket emit with animation data
                                socketio.emit('new_sms', {
                                    **sms,
                                    'animation': f"slideInRight-{sms['platform']}"
                                })
                                
                        logger.info(f"Processed {processed_count} new SMS")
                        
                        # Emit batch update with animation info
                        socketio.emit('data_update', {
                            'total_sms': len(data_storage.live_sms_data),
                            'platform_counts': dict(data_storage.platform_counts),
                            'last_update': datetime.now().isoformat(),
                            'animations': animation_data,
                            'theme': data_storage.theme
                        })
                        
                        # Special animation for batch
                        if processed_count > 0:
                            socketio.emit('batch_animation', {
                                'count': processed_count,
                                'platform_breakdown': animation_data
                            })
                        
                    retry_count = 0
                    
                else:
                    logger.warning("Not logged in, retrying login...")
                    retry_count += 1
                    
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                retry_count += 1
                
            if retry_count > 0:
                delay = min(self.retry_delay * (2 ** (retry_count - 1)), 300)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                time.sleep(self.fetch_interval)

# Initialize scraper
ivas_scraper = IVASRealTimeScraper()

# Flask Routes
@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index.html', 
                         theme=data_storage.theme,
                         colors=COLOR_THEMES[data_storage.theme],
                         platform_colors=PLATFORM_COLORS,
                         platform_gradients=PLATFORM_GRADIENTS)

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('index.html',
                         theme=data_storage.theme,
                         colors=COLOR_THEMES[data_storage.theme],
                         platform_colors=PLATFORM_COLORS,
                         platform_gradients=PLATFORM_GRADIENTS)

@app.route('/api/status')
def api_status():
    """Get system status"""
    return jsonify({
        'status': 'online',
        'logged_in': ivas_scraper.logged_in,
        'last_fetch': ivas_scraper.last_successful_fetch.isoformat() if ivas_scraper.last_successful_fetch else None,
        'total_sms': len(data_storage.live_sms_data),
        'platform_counts': dict(data_storage.platform_counts),
        'unique_countries': len(data_storage.country_counts),
        'monitoring_active': ivas_scraper.active,
        'theme': data_storage.theme,
        'analytics': data_storage.analytics,
        'fetch_count': ivas_scraper.fetch_count
    })

@app.route('/api/live-sms')
def get_live_sms():
    """Get live SMS data"""
    try:
        platform_filter = request.args.get('platform', 'all')
        country_filter = request.args.get('country', 'all')
        limit = int(request.args.get('limit', 50))
        
        sms_list = []
        for sms in list(data_storage.live_sms_data)[:1000]:
            if platform_filter != 'all' and sms.get('platform') != platform_filter:
                continue
            if country_filter != 'all' and sms.get('country') != country_filter:
                continue
            sms_list.append(sms)
            if len(sms_list) >= limit:
                break
                
        return jsonify({
            'success': True,
            'data': sms_list,
            'total': len(data_storage.live_sms_data),
            'filtered': len(sms_list),
            'last_update': data_storage.last_update_time.isoformat() if data_storage.last_update_time else None,
            'theme': data_storage.theme,
            'colors': COLOR_THEMES[data_storage.theme]
        })
        
    except Exception as e:
        logger.error(f"Error in get_live_sms: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get comprehensive statistics"""
    try:
        total_sms = sum(data_storage.platform_counts.values())
        
        stats = {}
        for platform in ['facebook', 'whatsapp', 'instagram']:
            count = data_storage.platform_counts[platform]
            percentage = (count / total_sms * 100) if total_sms > 0 else 0
            stats[platform] = {
                'count': count,
                'percentage': round(percentage, 2),
                'color': PLATFORM_COLORS[platform],
                'gradient': PLATFORM_GRADIENTS[platform]
            }
            
        top_countries = data_storage.get_top_countries(10)
        platform_percentages = data_storage.get_platform_percentages()
        
        return jsonify({
            'success': True,
            'platform_stats': stats,
            'top_countries': top_countries,
            'total_sms': total_sms,
            'unique_countries': len(data_storage.country_counts),
            'hourly_stats': data_storage.get_hourly_stats(6),
            'connection_status': data_storage.connection_status,
            'platform_percentages': platform_percentages,
            'analytics': data_storage.analytics,
            'theme': data_storage.theme,
            'theme_colors': COLOR_THEMES[data_storage.theme]
        })
        
    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/theme/<theme_name>')
def set_theme(theme_name):
    """Set color theme"""
    if data_storage.set_theme(theme_name):
        return jsonify({
            'success': True,
            'theme': theme_name,
            'colors': COLOR_THEMES[theme_name]
        })
    return jsonify({'success': False, 'error': 'Invalid theme'}), 400

@app.route('/api/refresh')
def refresh_data():
    """Manually refresh data from IVAS"""
    try:
        logger.info("Manual refresh requested")
        
        if not ivas_scraper.logged_in:
            if not ivas_scraper.login_with_cookies():
                return jsonify({'success': False, 'error': 'Login failed'}), 401
                
        new_sms = ivas_scraper.fetch_live_test_sms()
        processed = 0
        animation_data = {'facebook': 0, 'whatsapp': 0, 'instagram': 0}
        
        for sms in new_sms:
            if data_storage.add_sms(sms):
                processed += 1
                animation_data[sms['platform']] += 1
                socketio.emit('new_sms', {
                    **sms,
                    'animation': f"bounceIn-{sms['platform']}"
                })
                
        # Emit refresh animation
        socketio.emit('refresh_animation', {
            'count': processed,
            'platform_breakdown': animation_data
        })
                
        return jsonify({
            'success': True,
            'message': f'Refreshed {processed} new SMS',
            'count': processed,
            'total_sms': len(data_storage.live_sms_data),
            'animations': animation_data
        })
        
    except Exception as e:
        logger.error(f"Error in refresh_data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear')
def clear_data():
    """Clear all stored data"""
    try:
        data_storage.clear()
        logger.info("Data cleared")
        socketio.emit('clear_animation', {'action': 'clear'})
        return jsonify({
            'success': True,
            'message': 'All data cleared'
        })
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start-monitoring')
def start_monitoring():
    """Start real-time monitoring"""
    try:
        if not ivas_scraper.active:
            ivas_scraper.start_monitoring()
            
        socketio.emit('monitoring_started', {
            'active': True,
            'message': 'Real-time monitoring started'
        })
            
        return jsonify({
            'success': True,
            'message': 'Monitoring started',
            'active': ivas_scraper.active
        })
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop-monitoring')
def stop_monitoring():
    """Stop real-time monitoring"""
    try:
        ivas_scraper.stop_monitoring()
        socketio.emit('monitoring_stopped', {
            'active': False,
            'message': 'Real-time monitoring stopped'
        })
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped',
            'active': ivas_scraper.active
        })
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sms-stream')
def sms_stream():
    """Server-Sent Events stream for real-time SMS"""
    def generate():
        last_id = 0
        while True:
            if data_storage.last_update_time:
                current_time = datetime.now()
                time_diff = (current_time - data_storage.last_update_time).total_seconds()
                
                if time_diff < 60:
                    for sms in list(data_storage.live_sms_data)[:10]:
                        yield f"data: {json.dumps(sms)}\n\n"
                        
            time.sleep(5)
            
    return Response(generate(), mimetype="text/event-stream")

# WebSocket Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client WebSocket connection"""
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")
    
    emit('connection_status', {
        'status': 'connected',
        'logged_in': ivas_scraper.logged_in,
        'total_sms': len(data_storage.live_sms_data),
        'theme': data_storage.theme,
        'colors': COLOR_THEMES[data_storage.theme]
    })
    
    recent_sms = list(data_storage.live_sms_data)[:50]
    emit('initial_data', {
        'sms_list': recent_sms,
        'platform_counts': dict(data_storage.platform_counts),
        'last_update': data_storage.last_update_time.isoformat() if data_storage.last_update_time else None,
        'theme': data_storage.theme,
        'colors': COLOR_THEMES[data_storage.theme]
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_update')
def handle_update_request():
    """Handle update request from client"""
    emit('data_update', {
        'total_sms': len(data_storage.live_sms_data),
        'platform_counts': dict(data_storage.platform_counts),
        'last_update': datetime.now().isoformat(),
        'theme': data_storage.theme,
        'colors': COLOR_THEMES[data_storage.theme]
    })

@socketio.on('filter_sms')
def handle_filter_sms(data):
    """Handle SMS filter request"""
    platform = data.get('platform', 'all')
    country = data.get('country', 'all')
    
    filtered_sms = []
    for sms in list(data_storage.live_sms_data)[:100]:
        if platform != 'all' and sms.get('platform') != platform:
            continue
        if country != 'all' and sms.get('country') != country:
            continue
        filtered_sms.append(sms)
        
    emit('filtered_data', {
        'sms_list': filtered_sms,
        'platform': platform,
        'country': country,
        'count': len(filtered_sms)
    })

@socketio.on('change_theme')
def handle_change_theme(data):
    """Handle theme change request"""
    theme = data.get('theme', 'neon')
    if data_storage.set_theme(theme):
        emit('theme_changed', {
            'theme': theme,
            'colors': COLOR_THEMES[theme]
        })

# Initialize and start
def initialize_system():
    """Initialize the system"""
    logger.info("Initializing IVAS SMS Analytics System...")
    
    if ivas_scraper.login_with_cookies():
        logger.info("Successfully logged into IVAS")
        
        initial_sms = ivas_scraper.fetch_live_test_sms()
        if initial_sms:
            for sms in initial_sms:
                data_storage.add_sms(sms)
            logger.info(f"Loaded {len(initial_sms)} initial SMS records")
            
        ivas_scraper.start_monitoring()
    else:
        logger.error("Failed to login to IVAS")
        ivas_scraper.start_monitoring()

if __name__ == '__main__':
    initialize_system()
    
    logger.info("Starting IVAS SMS Analytics Dashboard...")
    logger.info(f"Dashboard URL: http://localhost:5000")
    
    socketio.run(app, 
                 debug=True, 
                 port=5000, 
                 host='0.0.0.0',
                 allow_unsafe_werkzeug=True,

                 log_output=True)
