
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from vocab_app.models import Word, UserWordInfo
from vocab_app import services
import pandas as pd
import numpy as np

class Command(BaseCommand):
    help = 'Populates the database with initial 100 words and sentences'

    def handle(self, *args, **kwargs):
        # 1. Create Superuser
        user, created = User.objects.get_or_create(username='admin')
        if created:
            user.set_password('password')
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created'))
        else:
            self.stdout.write('Superuser "admin" already exists')

        # 2. Define Data
        words_data = {
            "thai": [
                "ฉัน","คุณ","เขา","เธอ","เรา","พวกเรา","พวกเขา","นี่","นั่น","ที่นี่",
                "ที่นั่น","อะไร","ใคร","ที่ไหน","เมื่อไหร่","ทำไม","อย่างไร","ใช่","ไม่","ได้",
                "มี","ไม่มี","เป็น","อยู่","ไป","มา","กลับ","เข้า","ออก","ทำ",
                "พูด","ฟัง","ดู","อ่าน","เขียน","เรียน","สอน","รู้","เข้าใจ","คิด",
                "ชอบ","รัก","อยาก","ต้อง","สามารถ","ช่วย","ให้","เอา","ซื้อ","ขาย",
                "กิน","ดื่ม","นอน","ตื่น","เดิน","วิ่ง","นั่ง","ยืน","เปิด","ปิด",
                "เริ่ม","หยุด","เร็ว","ช้า","ดี","แย่","สวย","ใหญ่","เล็ก","มาก",
                "น้อย","ใหม่","เก่า","ร้อน","หนาว","วันนี้","พรุ่งนี้","เมื่อวาน","ตอนนี้","เช้า",
                "บ่าย","เย็น","กลางคืน","เวลา","วัน","ปี","บ้าน","ห้อง","โรงเรียน","งาน",
                "เงิน","อาหาร","น้ำ","ข้าว","รถ","ห้องน้ำ","ขอโทษ","ขอบคุณ","สวัสดี","ลาก่อน"
            ],
            "french": [
                "je","vous/tu","il/elle","elle","nous/on","nous","ils/elles","ceci","cela","ici",
                "là-bas","quoi","qui","où","quand","pourquoi","comment","oui","non","possible",
                "avoir","ne pas avoir","être","être (se trouver)","aller","venir","retourner","entrer","sortir","faire",
                "parler","écouter","regarder","lire","écrire","étudier","enseigner","savoir","comprendre","penser",
                "aimer (bien)","aimer","vouloir","devoir","être capable","aider","donner","prendre","acheter","vendre",
                "manger","boire","dormir","se réveiller","marcher","courir","s’asseoir","se tenir debout","ouvrir","fermer",
                "commencer","arrêter","rapide","lent","bon","mauvais","beau/belle","grand","petit","beaucoup",
                "peu","nouveau","vieux","chaud","froid","aujourd’hui","demain","hier","maintenant","matin",
                "après-midi","soir","nuit","temps/heure","jour","année","maison","chambre/pièce","école","travail",
                "argent","nourriture","eau","riz","voiture","toilettes","désolé/pardon","merci","bonjour","au revoir"
            ]
        }

        fr_sentences = [
            "J'ai faim.", "Comment allez-vous ?", "Il aime manger des fruits.", "Elle est très belle.", "Nous allons partir en voyage.",
            "Nous sommes amis.", "Ils vont à l'école.", "Qu'est-ce que c'est ?", "C'est ma maison.", "Le temps est beau ici.",
            "C'est où là-bas ?", "Que faites-vous ?", "Qui est-il ?", "Où êtes-vous ?", "Quand viendrez-vous ?",
            "Pourquoi êtes-vous en retard ?", "Comment faire ?", "Oui, je suis d'accord.", "Je ne sais pas.", "Je peux le faire.",
            "J'ai de l'argent.", "Je n'ai pas le temps.", "Je suis étudiant.", "Il est à la maison.", "Je vais au marché.",
            "Il vient ici.", "Je vais rentrer à la maison.", "Entrez, s'il vous plaît.", "Il est sorti.", "Que fais-tu ?",
            "Il peut parler thaï.", "Écoutons de la musique.", "J'aime regarder des films.", "Il aime lire des livres.", "J'écris une lettre.",
            "J'apprends le français.", "Le professeur enseigne les mathématiques.", "Je connais la vérité.", "J'ai compris.", "Je pense à toi.",
            "J'aime les chats.", "J'aime ma mère.", "Je veux aller au Japon.", "Je dois aller travailler.", "Il sait nager.",
            "Aidez-moi, s'il vous plaît.", "Je lui donne un cadeau.", "Je prends celui-ci.", "J'achète des fruits.", "Il vend sa voiture.",
            "Je mange du riz.", "Je bois de l'eau.", "Je veux dormir.", "Je me réveille tôt.", "Je marche pour aller à l'école.",
            "Il aime courir.", "Asseyez-vous, s'il vous plaît.", "Il se tient là-bas.", "Ouvrez la porte, s'il vous plaît.", "Éteignez la lumière.",
            "Commençons.", "Arrêtez la voiture ici.", "Cette voiture roule vite.", "Parlez lentement, s'il vous plaît.", "Cette nourriture est très bonne.",
            "Le temps est mauvais aujourd'hui.", "Cette fleur est belle.", "Cette maison est grande.", "Ce chien est petit.", "Merci beaucoup.",
            "J'ai peu d'argent.", "J'ai de nouveaux vêtements.", "Ce livre est vieux.", "Il fait chaud aujourd'hui.", "J'ai froid.",
            "Aujourd'hui, c'est lundi.", "À demain.", "Hier, il a plu.", "Quelle heure est-il maintenant ?", "Boire du café le matin.",
            "On se voit l'après-midi.", "Dîner le soir.", "Dormir la nuit.", "Le temps est précieux.", "C'est une journée ensoleillée.",
            "Quelle année sommes-nous ?", "Je suis à la maison.", "Cette pièce est agréable.", "Il va à l'école.", "Mon travail est difficile.",
            "Je n'ai pas d'argent.", "La cuisine thaïlandaise est délicieuse.", "De l'eau, s'il vous plaît.", "J'aime manger du riz.", "Une voiture rouge.",
            "Où sont les toilettes ?", "Excusez-moi.", "Merci pour tout.", "Bonjour.", "Au revoir, à bientôt."
        ]

        # 3. Iterate and Populate
        self.stdout.write('Starting population... (This may take a while using LLM)')
        
        # Load models once
        th_model = services.get_thai_model()

        for i in range(len(words_data['thai'])):
            thai_word = words_data['thai'][i]
            french_word = words_data['french'][i]
            sentence = fr_sentences[i] if i < len(fr_sentences) else ""

            # Create or Update Word
            word_obj, created = Word.objects.get_or_create(
                thai=thai_word, 
                defaults={'french': french_word}
            )

            # Get or Create UserWordInfo
            uwi, uwi_created = UserWordInfo.objects.get_or_create(user=user, word=word_obj)
            
            # If newly created OR missing flashcard data (e.g. french_sentence)
            if uwi_created or 'french_sentence' not in uwi.flashcard_infos:
                self.stdout.write(f'Refreshing info for: {thai_word}')
                try:
                    uwi.flashcard_infos = services.get_flashcard_infos(thai_word, french_word, sentence)
                    uwi.save()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error generating info for {thai_word}: {e}'))

        # 4. Update Coordinates & Clusters
        self.stdout.write('Updating 3D Map (Normalized) and Clusters...')
        all_user_infos = UserWordInfo.objects.filter(user=user).select_related('word')
        valid_infos = []
        vectors = []

        for uwi in all_user_infos:
            w_text = uwi.word.thai
            if w_text in th_model.key_to_index:
                valid_infos.append(uwi)
                vectors.append(th_model.get_vector(w_text))

        if len(vectors) > 2:
            # Optimized: UMAP -> Normalization -> Spacing Optimization
            optimized_coords = services.get_optimized_3d_coordinates(vectors)
            
            word_to_cluster, cluster_labels = services.auto_clustering([u.word.thai for u in valid_infos])

            to_update = []
            for i, uwi in enumerate(valid_infos):
                uwi.x = float(optimized_coords[i][0])
                uwi.y = float(optimized_coords[i][1])
                uwi.z = float(optimized_coords[i][2])
                
                c_id = word_to_cluster.get(uwi.word.thai)
                if c_id:
                    uwi.cluster_id = c_id
                    uwi.cluster_label = cluster_labels.get(c_id, "General")
                
                to_update.append(uwi)
            
            UserWordInfo.objects.bulk_update(to_update, ['x', 'y', 'z', 'cluster_id', 'cluster_label'])
            self.stdout.write(self.style.SUCCESS('Map updated successfully'))
        else:
            self.stdout.write(self.style.WARNING('Not enough vectors to update map'))

        self.stdout.write(self.style.SUCCESS('Database population/update finished!'))
