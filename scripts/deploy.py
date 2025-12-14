#!/usr/bin/env python3
"""
Script de deploy para o Geek Content Generator.
Automatiza o processo de deploy em diferentes ambientes.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from loguru import logger

class DeployManager:
    """
    Gerenciador de deploy para diferentes ambientes.
    """
    
    def __init__(self, environment: str):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        
    def deploy(self):
        """Executa deploy completo."""
        logger.info(f"Iniciando deploy para ambiente: {self.environment}")
        
        try:
            # Validações pré-deploy
            self._pre_deploy_checks()
            
            # Build das imagens
            self._build_images()
            
            # Deploy dos serviços
            self._deploy_services()
            
            # Verificações pós-deploy
            self._post_deploy_checks()
            
            logger.info("✅ Deploy concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro no deploy: {e}")
            sys.exit(1)
            
    def _pre_deploy_checks(self):
        """Validações antes do deploy."""
        logger.info("Executando verificações pré-deploy...")
        
        # Verifica se Docker está instalado
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Docker não está instalado ou não está acessível")
            
        # Verifica se Docker Compose está instalado
        try:
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Docker Compose não está instalado")
            
        # Verifica se arquivo docker-compose.yml existe
        if not self.docker_compose_file.exists():
            raise Exception(f"Arquivo {self.docker_compose_file} não encontrado")
            
        # Verifica variáveis de ambiente necessárias
        required_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        for var in required_vars:
            if not os.getenv(var):
                logger.warning(f"Variável de ambiente {var} não configurada")
                
        logger.info("✅ Verificações pré-deploy concluídas")
        
    def _build_images(self):
        """Build das imagens Docker."""
        logger.info("Building imagens Docker...")
        
        try:
            cmd = ["docker-compose", "build", "--no-cache"]
            subprocess.run(cmd, cwd=self.project_root, check=True)
            logger.info("✅ Imagens construídas com sucesso")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro ao construir imagens: {e}")
            
    def _deploy_services(self):
        """Deploy dos serviços."""
        logger.info("Fazendo deploy dos serviços...")
        
        try:
            # Para serviços existentes
            subprocess.run(
                ["docker-compose", "down"], 
                cwd=self.project_root, 
                check=False  # Não falha se não há containers rodando
            )
            
            # Inicia novos serviços
            cmd = ["docker-compose", "up", "-d"]
            
            if self.environment == 'production':
                cmd.extend(["--scale", "celery-worker=2"])
                
            subprocess.run(cmd, cwd=self.project_root, check=True)
            
            logger.info("✅ Serviços deployados com sucesso")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro no deploy dos serviços: {e}")
            
    def _post_deploy_checks(self):
        """Verificações pós-deploy."""
        logger.info("Executando verificações pós-deploy...")
        
        import time
        import requests
        
        # Aguarda serviços subirem
        logger.info("Aguardando serviços iniciarem...")
        time.sleep(30)
        
        # Testa health check
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Health check passou")
            else:
                raise Exception(f"Health check falhou: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro no health check: {e}")
            
        # Testa API
        try:
            response = requests.get("http://localhost:8000/api/v1/content/trending?limit=1", timeout=10)
            if response.status_code == 200:
                logger.info("✅ API está respondendo")
            else:
                logger.warning(f"API retornou status {response.status_code}")
                
        except requests.exceptions.RequestException:
            logger.warning("API pode não estar totalmente disponível ainda")
            
        # Verifica logs dos containers
        self._check_container_logs()
        
        logger.info("✅ Verificações pós-deploy concluídas")
        
    def _check_container_logs(self):
        """Verifica logs dos containers para erros."""
        logger.info("Verificando logs dos containers...")
        
        containers = [
            "geek-content-generator",
            "geek-content-worker", 
            "geek-content-scheduler"
        ]
        
        for container in containers:
            try:
                result = subprocess.run(
                    ["docker", "logs", "--tail", "50", container],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if "ERROR" in result.stderr.upper() or "CRITICAL" in result.stderr.upper():
                    logger.warning(f"Possíveis erros no container {container}")
                    logger.warning(result.stderr[-500:])  # Últimas 500 chars
                else:
                    logger.info(f"✅ Container {container} sem erros críticos")
                    
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                logger.warning(f"Não foi possível verificar logs do {container}")
                
    def rollback(self):
        """Executa rollback para versão anterior."""
        logger.info("Executando rollback...")
        
        try:
            # Para serviços atuais
            subprocess.run(
                ["docker-compose", "down"], 
                cwd=self.project_root, 
                check=True
            )
            
            # Aqui você implementaria a lógica para voltar à versão anterior
            # Por exemplo, usando tags de imagem ou backups
            
            logger.info("✅ Rollback concluído")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no rollback: {e}")
            
    def status(self):
        """Mostra status dos serviços."""
        logger.info("Status dos serviços:")
        
        try:
            result = subprocess.run(
                ["docker-compose", "ps"], 
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao obter status: {e}")
            
    def logs(self, service: str = None, follow: bool = False):
        """Mostra logs dos serviços."""
        cmd = ["docker-compose", "logs"]
        
        if follow:
            cmd.append("-f")
            
        if service:
            cmd.append(service)
            
        try:
            subprocess.run(cmd, cwd=self.project_root)
            
        except KeyboardInterrupt:
            logger.info("\nVisualizador de logs interrompido")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao obter logs: {e}")
            
def main():
    parser = argparse.ArgumentParser(description="Deploy Manager para Geek Content Generator")
    
    parser.add_argument(
        "action", 
        choices=["deploy", "rollback", "status", "logs"],
        help="Ação a ser executada"
    )
    
    parser.add_argument(
        "--environment", 
        choices=["development", "staging", "production"],
        default="development",
        help="Ambiente de deploy"
    )
    
    parser.add_argument(
        "--service",
        help="Serviço específico para logs"
    )
    
    parser.add_argument(
        "--follow", "-f",
        action="store_true",
        help="Seguir logs em tempo real"
    )
    
    args = parser.parse_args()
    
    deploy_manager = DeployManager(args.environment)
    
    if args.action == "deploy":
        deploy_manager.deploy()
    elif args.action == "rollback":
        deploy_manager.rollback()
    elif args.action == "status":
        deploy_manager.status()
    elif args.action == "logs":
        deploy_manager.logs(args.service, args.follow)
        
if __name__ == "__main__":
    main()