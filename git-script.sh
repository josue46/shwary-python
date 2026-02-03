git remote add origin https://github.com/josue46/shwary-python.git
git branch -M main
git add .

git commit -m "feat: initial release of Shwary Python SDK v1.0.1

- Implement Shwary and ShwaryAsync clients using httpx
- Add initiate_payment and get_transaction methods
- Robust validation with Pydantic V2 (E.164 phones, min amounts)
- Exception-based error handling (AuthenticationError, ValidationError)
- Full test suite with respx
- Modern project management with uv and hatchling"

git push -u origin main

