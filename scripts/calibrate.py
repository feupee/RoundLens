"""Ajuste afim por mínimos quadrados sem dependências extras.
Entrada JSON: lista de ao menos 3 pares {x,y,u,v}; u,v em [0,1] na imagem.
Use pontos adicionais distribuídos pelo mapa para validar, não apenas os de ajuste.
"""
import argparse,json,math

def solve(a,b):
    m=[list(row)+[value] for row,value in zip(a,b)]
    for i in range(3):
        pivot=max(range(i,3),key=lambda j:abs(m[j][i]))
        if abs(m[pivot][i])<1e-12:raise ValueError('Pontos colineares ou insuficientes')
        m[i],m[pivot]=m[pivot],m[i]
        factor=m[i][i];m[i]=[v/factor for v in m[i]]
        for j in range(3):
            if j!=i:
                factor=m[j][i];m[j]=[x-factor*y for x,y in zip(m[j],m[i])]
    return [r[3] for r in m]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('points');args=p.parse_args()
    points=json.load(open(args.points,encoding='utf-8'))
    if len(points)<3:raise ValueError('São necessários ao menos três pares')
    if not all(all(math.isfinite(float(r[k])) for k in ['x','y','u','v']) for r in points):raise ValueError('Valores inválidos')
    if not all(0<=r[k]<=1 for r in points for k in ['u','v']):raise ValueError('u/v devem estar em [0,1]')
    xs=[r['x'] for r in points];ys=[r['y'] for r in points]
    mx=sum(xs)/len(xs);my=sum(ys)/len(ys);scale=max(max(xs)-min(xs),max(ys)-min(ys),1)
    rows=[[(r['x']-mx)/scale,(r['y']-my)/scale,1] for r in points]
    a=[[sum(r[i]*r[j] for r in rows) for j in range(3)] for i in range(3)]
    coeff=[]
    for key in ['u','v']:
        b=[sum(r[i]*point[key] for r,point in zip(rows,points)) for i in range(3)]
        x,y,c=solve(a,b);coeff.extend([x/scale,y/scale,c-x*mx/scale-y*my/scale])
    print('Coeficientes para a interface:');print(', '.join(f'{v:.12g}' for v in coeff))
    errors=[math.hypot(coeff[0]*p['x']+coeff[1]*p['y']+coeff[2]-p['u'],coeff[3]*p['x']+coeff[4]*p['y']+coeff[5]-p['v']) for p in points]
    print('Erro RMS normalizado nos pontos usados:',math.sqrt(sum(e*e for e in errors)/len(errors)))
