/**
 * Public Homepage — About, Features, Pricing.
 */
import { GraduationCap, MessageCircle, BarChart3, Shield, Smartphone, IndianRupee } from 'lucide-react';

export function HomePage() {
  return (
    <div className="min-h-screen bg-surface-950">
      {/* Hero */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-brand-600/20 via-surface-950 to-surface-950" />
        <div className="relative max-w-6xl mx-auto px-6 pt-8 pb-20">
          <nav className="flex justify-between items-center mb-20">
            <h1 className="text-2xl font-bold font-marathi bg-gradient-to-r from-brand-400 to-brand-600 bg-clip-text text-transparent">
              विद्यामित्र
            </h1>
            <a
              href="/login"
              className="btn-primary text-sm px-5 py-2"
            >
              लॉगिन / साइन अप
            </a>
          </nav>

          <div className="text-center max-w-3xl mx-auto">
            <div className="text-6xl mb-6">🎓</div>
            <h2 className="text-4xl md:text-5xl font-bold font-marathi leading-tight mb-6">
              <span className="bg-gradient-to-r from-brand-400 via-brand-500 to-purple-500 bg-clip-text text-transparent">
                AI शिक्षण मंच
              </span>
              <br />
              <span className="text-white/90">मराठी माध्यम विद्यार्थ्यांसाठी</span>
            </h2>
            <p className="text-xl text-white/60 font-marathi mb-8 leading-relaxed">
              विद्यामित्र — तुमचा AI गुरू, मराठीत. अभ्यासक्रमानुसार शिकवणी,
              चाचण्या, प्रगती ट्रॅकिंग आणि पालकांसाठी साप्ताहिक WhatsApp अहवाल.
            </p>
            <div className="flex justify-center gap-4">
              <a href="/login" className="btn-primary text-lg px-8 py-4">
                सुरू करा — मोफत 🚀
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h3 className="text-3xl font-bold text-center mb-12 font-marathi">वैशिष्ट्ये</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { icon: <MessageCircle size={32} />, title: 'AI गुरू', desc: 'मराठीत टेक्स्ट आणि व्हॉइस चॅट — अभ्यासक्रमानुसार शिकवणी' },
            { icon: <GraduationCap size={32} />, title: 'अभ्यासक्रम ब्राउझर', desc: 'विषय → अध्याय → विषय — सर्व महाराष्ट्र बोर्ड अभ्यासक्रम' },
            { icon: <BarChart3 size={32} />, title: 'प्रगती ट्रॅकिंग', desc: 'शिक्षक आणि पालकांसाठी सामर्थ्य/कमकुवतपणा विश्लेषण' },
            { icon: <Smartphone size={32} />, title: 'मोबाइल-फर्स्ट', desc: 'फोनवर इन्स्टॉल करा — app store ची गरज नाही' },
            { icon: <Shield size={32} />, title: 'सुरक्षित', desc: 'पालक/शिक्षक दृश्यतेसह बाल सुरक्षा' },
            { icon: <IndianRupee size={32} />, title: 'कमी किमतीत', desc: 'कमी किमतीत दर्जेदार शिक्षण — सोलापूर पायलट' },
          ].map((f) => (
            <div key={f.title} className="glass-card p-6 hover:border-white/20 transition-all duration-300 group">
              <div className="text-brand-400 mb-4 group-hover:text-brand-300 transition-colors">{f.icon}</div>
              <h4 className="font-semibold text-lg mb-2 font-marathi">{f.title}</h4>
              <p className="text-white/50 text-sm font-marathi">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-white/30 text-sm">
        <p className="font-marathi">© 2026 विद्यामित्र • सोलापूर, महाराष्ट्र</p>
        <div className="flex justify-center gap-6 mt-4">
          <a href="#" className="hover:text-white/60 transition-colors">About Us</a>
          <a href="#" className="hover:text-white/60 transition-colors">Terms</a>
          <a href="#" className="hover:text-white/60 transition-colors">Refund Policy</a>
          <a href="#" className="hover:text-white/60 transition-colors">Privacy</a>
        </div>
      </footer>
    </div>
  );
}
