import numpy as np

def calculate_angle(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """Calcola l'angolo in gradi tra 3 punti (a, b, c) con vertice in b.
    
    Args:
        a: (x, y) del primo punto
        b: (x, y) del vertice dell'angolo
        c: (x, y) del secondo punto
        
    Returns:
        Angolo in gradi tra 0 e 180.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360.0 - angle
        
    return angle
