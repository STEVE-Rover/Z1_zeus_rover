function int_f = integration_simpson(X, F)
%INT�GRATION NUM�RIQUE PAR LA M�THODE DE SIMPSON
%   QUOI?
%       Sommation des valeurs du sur toute la plage de donn�es.
%      
%   COMMENT?
%       1: Calcul de la longueur
%       2: Calcul des pas d'int�gration (H) en fonction des donn�es en X
%       3: Calculs diff�rents pour les premiers et derniers termes
%
%   POURQUOI?
%       Cette m�thode est la plus pr�cise et efficace car elle utilise la
%       m�thode des courbes polynomiales.
%   
%   PARAM�TRES
%       Input:  [X]:        La matrice du temps
%               [F]:        La matrice des donn�es � int�grer
%       Output: [int_f]:    La matrice des donn�es int�gr�es

%% Calcul du pas d'int�gration (H)
H = X(2) - X(1);
H = 0.0500;

%% R�nitialisation du r�gistre ''SOMME''
somme = 0;

%% Boucle for pour traiter chaque donn�e unes par unes
    for i=1:1:(length(X))
        
        %Modulo de l'index actuel pour d�terminer si il est pair ou non
        modulo = mod(i, 2);
        
        %Si l'index est le premier ou dernier caract�re, effectuer le calcul suivant
        if i == 1 || i == length(X)
            somme = somme + abs(F(i));
        else
            
            %Diff�rents calculs si le chiffre est pair (modulo = 0)
            if modulo == 0
                somme = somme + abs(4*F(i)); 
            else
                somme = somme + abs(2*F(i));
            end
        end
    end
    
    %% Retour de la valeur finale calcul�e
    int_f = (H/3) * somme;
end