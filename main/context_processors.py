from main.settings import API_VERSION


def extra(request):
    ec = {}
    ec.update({'api_version': get_api_version(request)})
    return {'ec': ec}

def get_api_version(request):
    return API_VERSION