import plotly.graph_objects as go
from ZooFS.baseoptimizationalgorithm import BaseOptimizationAlgorithm
import numpy as np 
import pandas as pd

class DragonFlyOptimization(BaseOptimizationAlgorithm):
    def __init__(self,objective_function,n_iteration=50,population_size=50,minimize=True):
        super().__init__(objective_function,n_iteration,population_size,minimize)

    def evaluate_fitness(self,model,X_train,y_train,X_valid,y_valid):
        scores =  []
        for i,individual in enumerate(self.individuals):
            chosen_features = [index for index in range(X_train.shape[1]) if individual[index]==1]
            X_train_copy = X_train.iloc[:,chosen_features]
            X_valid_copy = X_valid.iloc[:,chosen_features]
            score = self.objective_function(model,X_train_copy,y_train,X_valid_copy,y_valid)
            if not(self.minimize):
                score=-score
            if score< self.best_score:
                self.best_score=score
                self.best_score_dimension=individual
                self.best_dim=individual
            if score> self.worst_score:
                self.worst_score=score
                self.worst_dim=individual
            scores.append(score)
        return scores
        
    def _check_params(self,model,X_train,y_train,X_valid,y_valid,method):
        super()._check_params(model,X_train,y_train,X_valid,y_valid)
        if method not in ['linear','random','quadraic','sinusoidal']:
            raise ValueError(f"method accepts only linear,random,quadraic types ")

    def fit(self,model,X_train,y_train,X_valid,y_valid,method='sinusoidal',verbose=True):
        self._check_params(model,X_train,y_train,X_valid,y_valid,method) 

        kbest=self.population_size-1
        self.feature_list=np.array(list(X_train.columns))
        self.best_results_per_iteration={}
        self.best_score=np.inf
        self.worst_score=-np.inf
        self.worst_dim=np.ones(X_train.shape[1]) 
        self.best_dim=np.ones(X_train.shape[1]) 
        
        self.best_score_dimension=np.ones(X_train.shape[1])       
        delta_x=np.random.randint(0,2,size=(self.population_size,X_train.shape[1]))
             
        self.initialize_population(X_train)

        for i in range(self.n_iteration):
            
            self._check_individuals()
            
            self.fitness_scores=self.evaluate_fitness(model,X_train,y_train,X_valid,y_valid)                        
            #if not(self.minimize):
            #    self.fitness_scores=list(-np.array(self.fitness_scores))
            
            self.iteration_objective_score_monitor(i)
                
            if method=='linear':
                s=0.2-(0.2*((i+1)/self.n_iteration))
                e=0.1-(0.1*((i+1)/self.n_iteration))
                a=0.0+(0.2*((i+1)/self.n_iteration))
                c=0.0+(0.2*((i+1)/self.n_iteration))
                f=0.0+(2*((i+1)/self.n_iteration))
                w=0.9-(i+1)*(0.5)/(self.n_iteration)

            if method=='random':
                if 2*(i+1)<=self.n_iteration:
                    pct=0.1-(0.2*(i+1)/self.n_iteration)
                else:
                    pct=0
                w=0.9-(i+1)*(0.5)/(self.n_iteration)
                s=2*np.random.random()*pct
                a=2*np.random.random()*pct
                c=2*np.random.random()*pct
                f=2*np.random.random()
                e=pct

            if method=='quadraic':
                w=0.9-(i+1)*(0.5)/(self.n_iteration)
                s=0.2-(0.2*((i+1)/self.n_iteration))**2
                e=0.1-(0.1*((i+1)/self.n_iteration))**2
                a=0.0+(0.2*((i+1)/self.n_iteration))**2
                c=0.0+(0.2*((i+1)/self.n_iteration))**2
                f=0.0+(2*(i+1)/self.n_iteration)**2
                
            if method=='sinusoidal':
                beta=0.5
                w=0.9-(i+1)*(0.5)/(self.n_iteration)
                s=0.10+0.10*np.abs( np.cos( ((i+1)/self.n_iteration)*(4*np.pi-beta*np.pi)) )
                e=0.05+0.05*np.abs( np.cos( ((i+1)/self.n_iteration)*(4*np.pi-beta*np.pi)) )
                a=0.10-0.05*np.abs( np.cos( ((i+1)/self.n_iteration)*(4*np.pi-beta*np.pi)) )
                c=0.10-0.05*np.abs( np.cos( ((i+1)/self.n_iteration)*(4*np.pi-beta*np.pi)) )
                f=2-1*np.abs( np.cos( ((i+1)/self.n_iteration)*(4*np.pi-beta*np.pi)) )
        
            temp=individuals=self.individuals
            temp_2=(( (temp.reshape(temp.shape[0],1,temp.shape[1])-temp.reshape(1,temp.shape[0],temp.shape[1])).reshape(temp.shape[0]**2,temp.shape[1])**2) )
            temp_3=temp_2.reshape(temp.shape[0],temp.shape[0],temp.shape[1]).sum(axis=2)
            zz=np.argsort(temp_3) 
            cc=[ list(iter1[iter1!=iter2]) for iter1,iter2 in zip(zz,np.arange(temp.shape[0])) ]

            Si=-(np.repeat(individuals,kbest,axis=0).reshape(individuals.shape[0],kbest,individuals.shape[1])-individuals[np.array(cc)[:,:kbest]]).sum(axis=1)
            Ai=delta_x[np.array(cc)[:,:kbest]].sum(axis=1)/kbest
            Ci=(individuals[np.array(cc)[:,:kbest]].sum(axis=1)/kbest)-individuals
            Fi=self.best_score_dimension-self.individuals
            Ei=self.individuals+self.worst_dim

            delta_x=s*Si+a*Ai+c*Ci+f*Fi+e*Ei+w*delta_x
            delta_x=np.where(delta_x>6,6,delta_x)
            delta_x=np.where(delta_x<-6,-6,delta_x)
            T=abs(delta_x/np.sqrt(1+delta_x**2))
            self.individuals=np.where(np.random.uniform(size=(self.population_size,X_train.shape[1]))<T,np.logical_not(self.individuals).astype(int),individuals)
            
            self.verbose_results(verbose,i)
            self.best_feature_list=list(self.feature_list[np.where(self.best_dim)[0]])
        return self.best_feature_list 