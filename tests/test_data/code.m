% Generate dataset with some correlation

data = rand(50,30);

mu = [2 3];
sigma = [1 1.5; 1.5 3];
rng default  % For reproducibility
R = mvnrnd(mu,sigma,100);

n = 50;
rng('default') % for reproducibility

U = copularnd('Gaussian',[1 .8 .8; .8 1 .8; .8 .8 1],n);
figure
plot(U(:,1),U(:,2),'.b')
hold on
plot(U(:,1),U(:,3),'.r')
plot(U(:,2),U(:,3),'.g')
title('{\it\rho} = 0.8')

U = copularnd('Gaussian',[1 .4 .2 .2 .2; .4 1 .8 .8 .8; .2 .8 1 .3 .9; .2 .8 .3 1 .9; .2 .8 .9 .9 1], n);

U = copularnd('Gaussian',[1 .8 .4 .4 .4; .8 1 .4 .4 .4; .4 .4 1 .4 .4; .4 .4 .4 1 .4; .4 .4 .4 .4 1], n);

M = [1 0.9 0.8 0.7 0.6;...
     0.9 1 0.7 0.6 0.5;...
     0.8 0.7 1 0.9 0.8;... 
     0.7 0.6 0.9 1 0.7;...
     0.6 0.5 0.8 0.7 1];