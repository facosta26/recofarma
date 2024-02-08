from flask import Blueprint, json, make_response, render_template, request, session, current_app
from sqlalchemy import func
from flask_weasyprint import HTML, render_pdf
from urllib.parse import unquote
from io import BytesIO
from flask_qrcode import QRcode
from app.models.Models import Doctors, MedicalEspecialties, People, PeoplePrescription, Roles, Users, db, PeoplePrescriptionDetails
class C_Reports():
    qrcode = QRcode()
    report = Blueprint('report',__name__)
    @report.route('/print_proof_delivery')
    def print_proof_delivery():
        datos = ""
        # Obtener el parámetro de la URL
        medicamentos_encoded = request.args.get('medicamentos', '[]')

        # Decodificar y cargar la lista
        medicamentos = json.loads(unquote(medicamentos_encoded))

        if medicamentos:
            # Consulta para obtener los detalles de la prescripción
            subquery = (
                db.session.query(
                    func.sum(PeoplePrescriptionDetails.prde_quantity).label('total_quantity')
                )
                .filter(PeoplePrescriptionDetails.prde_id.in_(medicamentos))
                .subquery()
            )

            datos = (
                db.session.query(
                    PeoplePrescriptionDetails.prde_id,
                    PeoplePrescriptionDetails.prde_medicine,
                    PeoplePrescriptionDetails.prde_quantity,
                    PeoplePrescriptionDetails.prde_pepr_id,
                    PeoplePrescriptionDetails.prde_date_dispatched,
                    subquery.c.total_quantity
                )
                .filter(PeoplePrescriptionDetails.prde_id.in_(medicamentos))
            ).all()
            datos_persona = People.query.join(PeoplePrescription, PeoplePrescription.pepr_peop_id == People.peop_id).filter(PeoplePrescription.pepr_id == datos[0].prde_pepr_id).first()

        rendered_html = render_template('r_proof_delivery.html', datos=datos, datos_persona=datos_persona, base_url=request.url_root)

        # Crea un objeto WeasyPrint HTML desde el HTML renderizado
        html = HTML(string=rendered_html)

        # Genera el PDF
        pdf = html.write_pdf()

        # Crea una respuesta Flask con el PDF
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=output.pdf'

        return response
    
    
    @report.route('/print_proof_consulting')
    def print_proof_consulting():
        datos_doctor = ""
        datos_consulta = ""
        datos_persona = ""
        datos_prescripcion = ""
        img = ""
        # Obtener el parámetro de la URL
        consulta_encoded = request.args.get('consulta', '[]')

        # Decodificar y cargar la lista
        consulta = json.loads(unquote(consulta_encoded))

        if consulta:
            datos_consulta = PeoplePrescription.query.filter(PeoplePrescription.pepr_id == consulta).first()
            datos_doctor = Doctors.query.with_entities((People.peop_names+' '+People.peop_lastnames).label('doctor'), People.peop_gender.label('gender'), Doctors.doct_professional_registration.label('prof_reg')).join(People, People.peop_id == Doctors.doct_peop_id).filter(Doctors.doct_peop_id == datos_consulta.pepr_doct_id).first()
            datos_persona = People.query.join(PeoplePrescription, PeoplePrescription.pepr_peop_id == People.peop_id).filter(PeoplePrescription.pepr_id == consulta).first()
            datos_prescripcion = PeoplePrescriptionDetails.query.filter(PeoplePrescriptionDetails.prde_pepr_id == consulta).all()
            # URL o datos que deseas codificar en el código QR
            """ data = "https://example.com"

            # Genera el código QR con Flask-QRcode
            img = C_Reports.qrcode(data)
            print(img)
            # Guarda la imagen en un buffer de Bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0) """

        rendered_html = render_template('r_proof_consulting.html', qr_code=img, datos_consulta=datos_consulta, datos_persona=datos_persona, datos_prescripcion=datos_prescripcion, datos_doctor=datos_doctor, base_url=request.url_root)

        # Crea un objeto WeasyPrint HTML desde el HTML renderizado
        html = HTML(string=rendered_html)

        # Genera el PDF
        pdf = html.write_pdf()

        # Crea una respuesta Flask con el PDF
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=output.pdf'

        return response
    
    @report.route('/statistics')
    def statistics():
        return render_template('v_statistics.html', title="Módulo Estadístico")
    
    @report.route('/doctor_quantity')
    def doctor_quantity():
        doctor_active = Doctors.query.with_entities(func.count(Doctors.doct_id).label('quantity')).filter(Doctors.doct_state == 'A').first()
        doctor_inactive = Doctors.query.with_entities(func.count(Doctors.doct_id).label('quantity')).filter(Doctors.doct_state == 'I').first()
        return json.dumps({'quantity_active': doctor_active.quantity, 'quantity_inactive': doctor_inactive.quantity})
    
    @report.route('/doctor_quantity_especialties')
    def doctor_quantity_especialties():
        list_especialties = MedicalEspecialties.query.filter(MedicalEspecialties.mees_state == 'A').order_by(MedicalEspecialties.mees_desc).all()
        list_doctors = Doctors.query.with_entities(MedicalEspecialties.mees_desc.label('especialty'), func.count(Doctors.doct_id).label('quantity')).join(MedicalEspecialties, MedicalEspecialties.mees_id == Doctors.doct_mees_id).filter(Doctors.doct_state == 'A').group_by(MedicalEspecialties.mees_desc).order_by(MedicalEspecialties.mees_desc).all()
        especialties = [
            {
                'especialty': i.mees_desc,
            } for i in list_especialties
                        ]
        doctors = [
            {
                'especialty': i.especialty,
                'quantity': i.quantity,
            } for i in list_doctors
                        ]
        return json.dumps([
            {
                'especialties': especialties,
                'doctors': doctors,
            }
        ])
        
    @report.route('/user_quantity')
    def user_quantity():
        user_active = Users.query.with_entities(func.count(Users.user_id).label('quantity')).filter(Users.user_state == 'A').first()
        user_inactive = Users.query.with_entities(func.count(Users.user_id).label('quantity')).filter(Users.user_state == 'I').first()
        return json.dumps({'quantity_active': user_active.quantity, 'quantity_inactive': user_inactive.quantity})
    
    @report.route('/user_quantity_role')
    def user_quantity_role():
        list_roles = Roles.query.all()
        list_users = Users.query.with_entities(Roles.role_desc.label('role'), func.count(Users.user_id).label('quantity')).join(Roles, Roles.role_id == Users.user_role_id).group_by(Roles.role_desc).order_by(Roles.role_desc).all()
        roles = [
            {
                'role': i.role_desc,
            } for i in list_roles
                        ]
        users = [
            {
                "role": u.role,
                "quantity": u.quantity
            } for u in list_users
        ]
        return json.dumps([
            {
                'roles': roles,
                'users': users
            }
        ])
        
    @report.route('/people_quantity_gender')
    def people_quantity_gender():
        list_genders = People.query.with_entities(People.peop_gender.label('gender'), func.count(People.peop_id).label('quantity')).group_by(People.peop_gender).order_by(People.peop_gender).all()
        genders = [
            {
                'gender': i.gender,
                'quantity': i.quantity
            } for i in list_genders
        ]
        return json.dumps([
            {
                'genders': genders
            }
        ])