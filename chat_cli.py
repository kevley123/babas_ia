import asyncio
import json
import httpx
import sys

BASE_URL = "http://localhost:8000"

async def main():
    print("============================================================")
    print("🧠 Terminal de Pruebas de Babas V1 (Agente + UI Mock)")
    print("Asegúrate de que el servidor esté corriendo (python run.py)")
    print("Escribe 'salir' para terminar o 'memoria' para ver tu perfil")
    print("============================================================\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Verificar si el servidor está vivo
        try:
            await client.get(f"{BASE_URL}/health")
        except httpx.ConnectError:
            print("❌ Error: No se pudo conectar al servidor.")
            print("Por favor, abre otra terminal y ejecuta: python run.py")
            sys.exit(1)

        while True:
            try:
                user_input = input("Tú: ")
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input.strip():
                continue

            if user_input.strip().lower() in ["salir", "exit", "quit"]:
                print("Cerrando conexión...")
                break
                
            if user_input.strip().lower() == "memoria":
                print("\n[Consultando memoria de perfil...]")
                resp = await client.get(f"{BASE_URL}/profile")
                if resp.status_code == 200:
                    data = resp.json()
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"Error: {resp.status_code}")
                print()
                continue

            # Enviar mensaje a Babas
            print("Babas está pensando...")
            try:
                resp = await client.post(
                    f"{BASE_URL}/chat", 
                    json={"message": user_input}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Interfaz simulada
                    ui = data.get("ui", {})
                    avatar = ui.get("avatar", "neutral")
                    panels = ui.get("panels", ["chat"])
                    
                    print(f"\n[UI: Avatar={avatar} | Paneles={panels}]")
                    
                    # Simular Frontend ejecutando una herramienta
                    tool = data.get("tool", {})
                    if data.get("type") == "tool_call":
                        print(f"🛠️  [TOOL_CALL] Herramienta: {tool.get('name')} | Intent: {tool.get('intent')}")
                        params = tool.get("params", {})
                        if params:
                            print(f"   Parámetros: {json.dumps(params, ensure_ascii=False)}")
                        
                        # Simular reproducción en el frontend
                        if tool.get("intent") == "PLAY_PLAYLIST":
                            url = params.get("url")
                            if url:
                                print(f"🎶 [FRONTEND] Abriendo reproductor MPV con URL: {url}")
                            else:
                                print(f"🎶 [FRONTEND] Abriendo reproductor buscando: {params.get('name')}")
                        elif tool.get("intent") == "PLAY_SONG":
                            print("🎶 [FRONTEND] Reproduciendo canción solicitada...")
                            
                    print(f"🤖 Babas: {data.get('message')}")
                    print("-" * 60)
                else:
                    print(f"\n❌ Error del servidor: {resp.status_code}")
                    print(resp.text)
                    
            except httpx.ReadTimeout:
                print("\n❌ Error: El servidor tardó demasiado en responder.")
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())
