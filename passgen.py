from werkzeug.security import generate_password_hash

print('\nInput password:')
passw = input()
print(generate_password_hash(passw))