from flask import redirect

def setup(request, facebook_id):
    authorization_code = request.args.get('code')

    client_id = 'MEZC4SKNQBXGVTMXMW0IKILIW1RQ4CAZ5AOQROEB5JGLGGD0'
    client_secret = 'DZKA31MFCNC252LAAKV05XVQIWWM0IWBQCGQU3L2IEA43JJD'
    
    # Get access token
    # token_url = 'https://foursquare.com/oauth2/access_token?client_id='+client_id+'&client_secret='client_secret'&grant_type=authorization_code&redirect_uri=YOUR_REGISTERED_REDIRECT_URI&code=CODE'

    # Redirect to dashboard
    redirect_url = "/" + facebook_id
    return redirect(redirect_url)