"""
MILARIPPA - Serveur Flask
=========================
Interface web pour discuter avec Milarepa.
Historique sauvegardé dans Supabase.
"""

import os
import json
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from supabase import create_client
from rag import generate_response

load_dotenv()

app = Flask(__name__)

# Clients
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def get_user_id():
    """Récupère ou crée un ID utilisateur unique (basé sur l'IP)."""
    ip = request.remote_addr
    user_id = hashlib.md5(ip.encode()).hexdigest()[:16]
    return user_id


@app.route("/")
def index():
    return render_template("index.html")


# ===== ENDPOINTS CONVERSATIONS =====

@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    """Récupère toutes les conversations de l'utilisateur."""
    try:
        user_id = get_user_id()
        result = supabase.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversations", methods=["POST"])
def create_conversation():
    """Crée une nouvelle conversation."""
    try:
        user_id = get_user_id()
        data = request.json
        title = data.get("title", "Nouvelle conversation")
        
        result = supabase.table("conversations").insert({
            "user_id": user_id,
            "title": title
        }).execute()
        
        return jsonify(result.data[0]), 201
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversations/<conversation_id>/messages", methods=["GET"])
def get_messages(conversation_id):
    """Récupère tous les messages d'une conversation."""
    try:
        result = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        
        # Convertir sources JSON
        messages = []
        for msg in result.data:
            if msg.get("sources"):
                msg["sources"] = json.loads(msg["sources"]) if isinstance(msg["sources"], str) else msg["sources"]
            messages.append(msg)
        
        return jsonify(messages)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Supprime une conversation et ses messages."""
    try:
        supabase.table("conversations").delete().eq("id", conversation_id).execute()
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500


# ===== ENDPOINT CHAT =====

@app.route("/api/chat", methods=["POST"])
def chat():
    """Envoie un message et sauvegarde la conversation."""
    data = request.json
    question = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    
    if not question:
        return jsonify({"error": "Message vide"}), 400
    
    if not conversation_id:
        return jsonify({"error": "conversation_id manquant"}), 400
    
    try:
        # Récupérer l'historique des messages
        messages_result = supabase.table("messages").select("role, content").eq("conversation_id", conversation_id).order("created_at").execute()
        history = messages_result.data if messages_result.data else []
        
        # Générer la réponse RAG
        result = generate_response(question, history)
        
        # Sauvegarder le message utilisateur
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "user",
            "content": question
        }).execute()
        
        # Sauvegarder la réponse
        sources_json = json.dumps(result.get("sources", []))
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": result["answer"],
            "sources": sources_json
        }).execute()
        
        # Mettre à jour le titre si c'est le premier message
        conv = supabase.table("conversations").select("title").eq("id", conversation_id).execute()
        if conv.data and conv.data[0]["title"] == "Nouvelle conversation":
            title = question[:60].rstrip(".,!?") or "Nouvelle conversation"
            supabase.table("conversations").update({"title": title, "updated_at": datetime.utcnow().isoformat()}).eq("id", conversation_id).execute()
        else:
            supabase.table("conversations").update({"updated_at": datetime.utcnow().isoformat()}).eq("id", conversation_id).execute()
        
        return jsonify({
            "answer": result["answer"],
            "sources": result.get("sources", []),
        })
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print("🏔️  MILARIPPA - Converse avec Milarepa")
    print(f"🌐 http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
