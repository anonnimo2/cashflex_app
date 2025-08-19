from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp, Optional
from flask_wtf.file import FileField, FileAllowed


# Formulário de Login
class LoginForm(FlaskForm):
    phone = StringField('Número', validators=[
        DataRequired(message='Digite seu número.'),
        Length(min=9, message='Número muito curto.')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Digite sua senha.')
    ])
    submit = SubmitField('Entrar')


# Formulário de Cadastro
class RegisterForm(FlaskForm):
    phone = StringField('Número', validators=[
        DataRequired(message='Digite seu número.'),
        Length(min=9, message='Número inválido.')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Digite uma senha.')
    ])
    referred_by = StringField('Código de Convite (opcional)')
    submit = SubmitField('Cadastrar')


# Formulário de depósito
class DepositForm(FlaskForm):
    amount = FloatField('Valor do Investimento', validators=[
        DataRequired(message='Informe um valor.'),
        NumberRange(min=5000, message='Valor mínimo: 5000 AOA')
    ])

    payment_method = SelectField('Método de Pagamento', choices=[
        ('transferencia', 'Transferência Bancária'),

    ], validators=[DataRequired(message='Selecione um método de pagamento.')])

    bank = SelectField('Banco', choices=[
        ('BAI', 'BAI'),
        ('BCI', 'BCI'),
        ('Atlântico', 'Atlântico')
    ], validators=[DataRequired(message='Selecione um banco.')])

    proof = FileField('Comprovativo (JPG, PNG ou PDF)', validators=[
        DataRequired(message='Envie o comprovativo.'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Apenas JPG, PNG ou PDF!')
    ])

    submit = SubmitField('Depositar')


# Formulário de Saque
class WithdrawalForm(FlaskForm):
    amount = FloatField('Valor (mínimo 1200 Kz)', validators=[
        DataRequired(message='Informe um valor.'),
        NumberRange(min=1200, message='O valor mínimo é 1200 Kz')
    ])
    bank = SelectField('Banco', choices=[
        ('BAI', 'BAI'),
        ('BCI', 'BCI'),
        ('Atlântico', 'Atlântico')
    ], validators=[DataRequired(message='Selecione um banco.')])

    submit = SubmitField('Solicitar Retirada')



class ProfileForm(FlaskForm):
    bank = SelectField('Banco', choices=[('BAI', 'BAI'), ('BCI', 'BCI'), ('Atlântico', 'Atlântico')], validators=[DataRequired()])
    iban = StringField('IBAN', validators=[
        DataRequired(),
        Length(min=21, max=25, message='O IBAN deve conter entre 21 e 25 caracteres'),
        Regexp(r'^\d{21}$', message='Formato de IBAN inválido')
    ])
    iban_owner = StringField('Nome do Titular', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    submit = SubmitField('Salvar')
    
    
# forms.py
class PlanForm(FlaskForm):
    nome = StringField('Nome do Plano', validators=[DataRequired()])
    invest = FloatField('Valor de Investimento', validators=[DataRequired()])
    rendimento = FloatField('Rendimento Diário', validators=[DataRequired()])
    retorno = FloatField('Retorno Total', validators=[DataRequired()])
    ativo = BooleanField('Ativo?')
    submit = SubmitField('Salvar')


class SimpleActionForm(FlaskForm):
    submit = SubmitField('Enviar')
    
    
    
    
    
    