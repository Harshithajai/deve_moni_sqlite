import { useState } from 'react';

import {
  Link,
  useNavigate
} from 'react-router-dom';

import api from '../api';

import {
  tokenKey
} from '../auth';


function ConnectProfessionalPage() {

  const navigate = useNavigate();


  const [professionalId, setProfessionalId] = useState('');

  const [message, setMessage] = useState('');

  const [error, setError] = useState('');

  const [loading, setLoading] = useState(false);



  const handleConnect = async (event) => {

    event.preventDefault();


    setMessage('');

    setError('');


    if (
      !professionalId ||
      Number(professionalId) <= 0
    ) {

      setError(
        'Please enter a valid professional ID.'
      );

      return;
    }


    const token = localStorage.getItem(tokenKey);


    if (!token) {

      navigate('/login');

      return;
    }


    setLoading(true);


    try {

      const response = await api.post(

        '/api/parents/connect-professional',

        {
          professional_id: Number(professionalId)
        },

        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }

      );


      setMessage(

        response.data.message ||
        'Successfully connected with professional.'

      );


      setProfessionalId('');


    } catch (requestError) {

      if (
        requestError.response?.status === 401
      ) {

        setError(
          'Your session has expired. Please log in again.'
        );

        return;
      }


      setError(

        requestError.response?.data?.detail ||

        'Unable to connect with professional.'

      );


    } finally {

      setLoading(false);

    }

  };



  return (

    <div className="page-shell dashboard-shell">


      {/* Sidebar */}

      <aside className="sidebar">

        <div className="sidebar-brand">
          DevCare
        </div>


        <nav className="sidebar-nav">


          <Link
            to="/parent/dashboard"
            className="nav-item"
          >
            Dashboard
          </Link>


          <Link
            to="/parent/children"
            className="nav-item"
          >
            Children
          </Link>


          <Link
            to="/parent/observations"
            className="nav-item"
          >
            Observations
          </Link>


          <Link
            to="/parent/history"
            className="nav-item"
          >
            History
          </Link>


          <Link
            to="/parent/progress"
            className="nav-item"
          >
            Progress
          </Link>


          <Link
            to="/parent/assistant"
            className="nav-item"
          >
            Ask Assistant
          </Link>


          <Link
            to="/parent/connect-professional"
            className="nav-item active"
          >
            Connect Professional
          </Link>


        </nav>

      </aside>



      {/* Main Content */}

      <main className="dashboard-main">


        {/* Header */}

        <header className="dashboard-header">

          <div>

            <p className="eyebrow">
              Professional Connection
            </p>


            <h1>
              Connect with a Professional
            </h1>

          </div>


          <Link
            to="/parent/dashboard"
            className="secondary-btn"
          >
            Back to Dashboard
          </Link>

        </header>



        {/* Error Message */}

        {error && (

          <div className="error-box">

            {error}

          </div>

        )}



        {/* Connection Form */}

        <section className="summary-card form-card">


          <h3>
            Connect your account
          </h3>


          <p className="muted-text">

            Enter the professional ID provided
            by your therapist or other professional.

          </p>



          {/* Success Message */}

          {message && (

            <div className="success-box">

              {message}

            </div>

          )}



          {/* Form */}

          <form
            onSubmit={handleConnect}
          >


            <div className="form-group">


              <label
                htmlFor="professionalId"
              >

                Professional ID

              </label>



              <input

                id="professionalId"

                type="number"

                min="1"

                placeholder="Enter professional ID"

                value={professionalId}

                onChange={(event) => {

                  setProfessionalId(
                    event.target.value
                  );

                }}

                required

              />


            </div>



            <button

              type="submit"

              className="primary-btn"

              disabled={loading}

            >

              {loading
                ? 'Connecting...'
                : 'Connect'
              }

            </button>


          </form>


        </section>


      </main>


    </div>

  );

}


export default ConnectProfessionalPage;