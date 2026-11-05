import { useState, type FormEvent } from 'react'
import { usePreferencias } from '../lib/usePreferencias'
import { navegar } from '../lib/rotas'
import { Logo } from '../components/Layout'
import { ControlesPreferencias } from '../components/Preferencias'
import { Botao } from '../components/ui'

// Tela visual do protótipo: ainda não há autenticação. "Entrar" só abre o painel.
export function Login() {
  const { t } = usePreferencias()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')

  function entrar(evento: FormEvent) {
    evento.preventDefault()
    navegar('visao-geral')
  }

  return (
    <div className="flex min-h-dvh flex-col bg-superficie lg:flex-row">
      <section className="flex flex-col gap-6 bg-linear-to-br from-[#4f46e5] to-[#312e81] px-6 py-8 text-white sm:px-10 lg:w-[44%] lg:justify-between lg:px-16 lg:py-14">
        <div className="flex items-center justify-between gap-3">
          <Logo claro />
          <ControlesPreferencias sobreEscuro />
        </div>
        <div className="flex flex-col gap-4 lg:gap-6">
          <span className="w-fit rounded-full bg-white/15 px-3 py-1.5 text-xs font-semibold">{t.login.selo}</span>
          <h1 className="text-2xl font-bold leading-tight sm:text-3xl lg:text-[40px] lg:leading-[48px]">
            {t.login.titulo}
          </h1>
          <p className="hidden text-base leading-relaxed text-indigo-100 sm:block">{t.login.texto}</p>
        </div>
        <p className="hidden text-xs text-indigo-300 lg:block">{t.login.fonte}</p>
      </section>

      <section className="flex flex-1 items-start justify-center px-6 py-10 sm:items-center">
        <form onSubmit={entrar} className="flex w-full max-w-sm flex-col gap-5">
          <div>
            <h2 className="text-2xl font-bold sm:text-[28px]">{t.login.boasVindas}</h2>
            <p className="mt-2 text-sm text-suave">{t.login.instrucao}</p>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-[13px] font-medium text-texto-2">
              {t.login.email}
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t.login.emailExemplo}
              className="min-h-11 rounded-xl border border-borda bg-superficie px-3.5 text-sm text-texto placeholder:text-fraco"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="senha" className="text-[13px] font-medium text-texto-2">
              {t.login.senha}
            </label>
            <input
              id="senha"
              type="password"
              autoComplete="current-password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="min-h-11 rounded-xl border border-borda bg-superficie px-3.5 text-sm text-texto"
            />
          </div>
          <Botao type="submit">{t.login.entrar}</Botao>
          <p className="text-center text-xs text-suave">{t.login.aviso}</p>
        </form>
      </section>
    </div>
  )
}
