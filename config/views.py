from django.shortcuts import render

def custom_404(request, exception):
    context = {
        'error_code': '404',
        'error_title': '¡Fallo Crítico en Percepción!',
        'error_message': 'Has tirado un 1. El perfil, mesa o página que buscas no existe o se ha perdido en el abismo.',
        'error_icon': 'fa-ghost'
    }
    return render(request, 'error.html', context, status=404)

def custom_500(request):
    context = {
        'error_code': '500',
        'error_title': '¡El Servidor recibió Daño Masivo!',
        'error_message': 'Nuestros conjuros fallaron y el servidor se ha caído temporalmente. Los gnomos ingenieros ya están trabajando en ello.',
        'error_icon': 'fa-fire-alt'
    }
    return render(request, 'error.html', context, status=500)

def custom_403(request, exception):
    context = {
        'error_code': '403',
        'error_title': '¡Campo de Fuerza Mágico!',
        'error_message': 'No tienes los permisos necesarios (ni el nivel) para explorar esta zona.',
        'error_icon': 'fa-shield-alt'
    }
    return render(request, 'error.html', context, status=403)

def custom_400(request, exception):
    context = {
        'error_code': '400',
        'error_title': 'Conjuro Mal Formulado',
        'error_message': 'El servidor no pudo entender tu petición. Revisa si tu navegador hizo algo extraño.',
        'error_icon': 'fa-scroll'
    }
    return render(request, 'error.html', context, status=400)
