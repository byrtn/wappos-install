# Auteur : Patrick Ritaine
import app


def test_documentation_page_shows_superadmin_content(logged_in_client):
    resp = logged_in_client.get("/documentation")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "Docker Gate" in body
    assert "Creating a domain administrator" in body or "Créer un administrateur de domaine" in body


def test_documentation_page_shows_domain_admin_content():
    flask_app = app.app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = "domain.admin"
            sess["token"] = "test-token"
            sess["is_superadmin"] = False
            sess["owned_domains"] = ["dev.byrtn.fr"]
        resp = client.get("/documentation")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "administrateur de domaine" in body.lower() or "domain administrator" in body.lower()
    assert "Creating a domain administrator" not in body and "Créer un administrateur de domaine" not in body
