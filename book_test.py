import json, urllib.request, urllib.error
BASE="http://localhost:8000"
def tok(u):
    from app.services.jwt_service import create_access_token
    from app.database import SessionLocal
    from app.models.user import User
    db=SessionLocal(); us=db.query(User).filter(User.email==u).first()
    t=create_access_token(us.id, us.role.name); db.close(); return t
ADM=tok("admin@af.com"); PRI=tok("priya@af.com")
def call(m,p,token=None,body=None):
    h={"Content-Type":"application/json"}
    if token: h["Authorization"]="Bearer "+token
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(BASE+p,data=data,headers=h,method=m)
    try:
        r=urllib.request.urlopen(req); return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e: return e.code, e.read().decode()

cat=call("GET","/org/asset-categories",ADM)[1][0]["id"]
rm=call("POST","/assets",ADM,{"name":"Meeting Room A","category_id":cat,"is_bookable":True,"condition":"good","location":"HQ"})[1]
print("bookable asset:", rm.get("asset_tag"), rm.get("id"), "is_bookable=", rm.get("is_bookable"))
aid=rm["id"]; d="2026-07-20"
b1=call("POST","/bookings",PRI,{"asset_id":aid,"start_time":f"{d}T09:00","end_time":f"{d}T10:00","purpose":"standup"})[1]
print("create booking (priya):", b1.get("id"), b1.get("status"), "resource=", b1.get("asset_name"))
bid=b1["id"]
s2=call("POST","/bookings",PRI,{"asset_id":aid,"start_time":f"{d}T09:30","end_time":f"{d}T11:00"})
print("conflict booking status:", s2[0], "->", (s2[1][:120] if isinstance(s2[1],str) else s2[1].get("detail")))
b3=call("POST","/bookings",PRI,{"asset_id":aid,"start_time":f"{d}T11:00","end_time":f"{d}T12:00"})[1]
print("non-overlap booking:", b3.get("id"), b3.get("status"))
print("list all count:", len(call("GET","/bookings",ADM)[1]))
print("list mine (priya):", len(call("GET","/bookings?mine=true",PRI)[1]))
c=call("POST",f"/bookings/{bid}/cancel",PRI)
print("cancel own booking:", c[0], c[1].get("status"))
c2=call("POST",f"/bookings/{b3['id']}/cancel",PRI)
print("cancel other (priya):", c2[0], c2[1].get("status"))
# dashboard active_bookings should reflect upcoming count
print("dashboard active_bookings:", call("GET","/dashboard",ADM)[1].get("active_bookings"))
