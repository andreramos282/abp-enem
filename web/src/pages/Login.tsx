import { useState, type FormEvent } from 'react'
import { navegar } from '../lib/rotas'
import { Logo } from '../components/Layout'
import { Botao } from '../components/ui'

// Tela visual do protótipo: ainda não há autenticação. "Entrar" só abre o painel.
export function Login() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')

  function entrar(evento: FormEvent) {
    evento.preventDefault()
    navegar('visao-geral')
  }

  return (
    <div className="flex min-h-dvh flex-col bg-white lg:flex-row">
      <section className="flex flex-col gap-6 bg-linear-to-br from-primaria to-[#312e81] px-6 py-8 text-white sm:px-10 lg:w-[44%] lg:justify-between lg:px-16 lg:py-14">
        <Logo claro />
        <div className="flex flex-col gap-4 lg:gap-6">
          <span className="w-fit rounded-full bg-white/15 px-3 py-1.5 text-xs font-semibold">
            Inteligência educacional para a rede pública
          </span>
          <h1 className="text-2xl font-bold leading-tight sm:text-3xl lg:text-[40px] lg:leading-[48px]">
            Antecipe quais alunos precisam de apoio antes do ENEM.
          </h1>
          <p className="hidden text-base leading-relaxed text-indigo-100 sm:block">
            Cruzamos dados socioeconômicos e escolares dos microdados do ENEM para apontar perfis com risco de baixo
            desempenho e sugerir onde intervir primeiro.
          </p>
        </div>
        <p className="hidden text-xs text-indigo-300 lg:block">Fonte dos dados: Microdados do ENEM · INEP</p>
      </section>

      <section className="flex flex-1 items-start justify-center px-6 py-10 sm:items-center">
        <form onSubmit={entrar} className="flex w-full max-w-sm flex-col gap-5">
          <div>
            <h2 className="text-2xl font-bold sm:text-[28px]">Bem-vindo de volta</h2>
            <p className="mt-2 text-sm text-suave">Entre com sua conta institucional para acessar o painel.</p>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-[13px] font-medium text-texto-2">
              E-mail institucional
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nome@escola.gov.br"
              className="min-h-11 rounded-xl border border-borda px-3.5 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="senha" className="text-[13px] font-medium text-texto-2">
              Senha
            </label>
            <input
              id="senha"
              type="password"
              autoComplete="current-password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="min-h-11 rounded-xl border border-borda px-3.5 text-sm"
            />
          </div>
          <Botao type="submit">Entrar</Botao>
          <p className="text-center text-xs text-suave">
            Protótipo acadêmico: o acesso ainda não exige cadastro.
          </p>
        </form>
      </section>
    </div>
  )
}
