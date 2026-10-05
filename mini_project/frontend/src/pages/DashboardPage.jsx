import { useEffect, useState } from 'react';

import {
  Link,
  useNavigate
} from 'react-router-dom';

import api from '../api';

import {
  tokenKey,
  logout
} from '../auth';

import ChildSelector from '../components/ChildSelector';

import LoadingSpinner from '../components/LoadingSpinner';

import ObservationCard from '../components/ObservationCard';

import ProgressChart from '../components/ProgressChart';

import StatCard from '../components/StatCard';



function DashboardPage() {


  const navigate = useNavigate();


  const [user, setUser] = useState(null);

  const [children, setChildren] = useState([]);

  const [selectedChildId, setSelectedChildId] = useState('');

  const [recentObservations, setRecentObservations] = useState([]);

  const [domainSummary, setDomainSummary] = useState([]);

  const [timelineData, setTimelineData] = useState([]);

  const [error, setError] = useState('');

  const [loading, setLoading] = useState(true);



  useEffect(() => {


    const token = localStorage.getItem(tokenKey);


    if (!token) {

      navigate('/login');

      return;

    }



    const fetchDashboard = async () => {


      try {


        const [
          userResponse,
          childrenResponse
        ] = await Promise.all([


          api.get(
            '/api/auth/me',
            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          ),


          api.get(
            '/api/children',
            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          )


        ]);



        setUser(userResponse.data);

        setChildren(childrenResponse.data);



        if (
          childrenResponse.data.length > 0
        ) {


          const firstChildId =
            childrenResponse.data[0].id;


          setSelectedChildId(
            String(firstChildId)
          );



          const progressResponse = await api.get(

            `/api/progress/${firstChildId}`,

            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }

          );



          setRecentObservations(

            progressResponse.data.recent_observations || []

          );


          setDomainSummary(

            progressResponse.data.domain_summary || []

          );


          setTimelineData(

            progressResponse.data.timeline || []

          );


        }


      } catch (requestError) {


        if (
          requestError.response?.status === 401
        ) {


          logout();

          navigate('/login');

          return;

        }



        setError(

          requestError.response?.data?.detail ||

          'Unable to load dashboard information.'

        );


      } finally {


        setLoading(false);


      }


    };



    fetchDashboard();


  }, [navigate]);



  useEffect(() => {


    const token = localStorage.getItem(tokenKey);


    if (
      !token ||
      !selectedChildId
    ) {

      return;

    }



    const fetchSelectedChildProgress = async () => {


      try {


        const response = await api.get(

          `/api/progress/${selectedChildId}`,

          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }

        );



        setRecentObservations(

          response.data.recent_observations || []

        );


        setDomainSummary(

          response.data.domain_summary || []

        );


        setTimelineData(

          response.data.timeline || []

        );



      } catch (requestError) {


        setError(

          requestError.response?.data?.detail ||

          'Unable to load child progress.'

        );


      }


    };



    fetchSelectedChildProgress();


  }, [selectedChildId]);



  const handleLogout = () => {


    logout();

    navigate('/login');


  };



  const domainChartData = domainSummary.map(

    (item) => ({

      name: item.domain,

      value: item.count

    })

  );



  const recentCards = recentObservations

    .slice(0, 4)

    .map((item) => ({

      ...item,

      date: new Date(

        item.observation_date

      ).toLocaleDateString()

    }));



  if (loading) {


    return (

      <div className="page-shell dashboard-shell">

        <LoadingSpinner
          message="Loading dashboard..."
        />

      </div>

    );

  }



  return (


    <div className="page-shell dashboard-shell">


      {/* Sidebar */}

      <aside className="sidebar">


        <div className="sidebar-brand">

          DevCare

        </div>



        <nav className="sidebar-nav">


          <button
            className="nav-item active"
          >

            Overview

          </button>



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



          {/* Connect Professional */}

          <Link
            to="/parent/connect-professional"
            className="nav-item"
          >

            Connect Professional

          </Link>



        </nav>


      </aside>



      {/* Main Dashboard */}

      <main className="dashboard-main">


        {/* Header */}

        <header className="dashboard-header">


          <div>


            <p className="eyebrow">

              Dashboard

            </p>



            <h1>

              Welcome, {user?.full_name || 'Caregiver'}

            </h1>


          </div>



          <button

            className="secondary-btn"

            onClick={handleLogout}

          >

            Logout

          </button>


        </header>



        {/* Error */}

        {error && (

          <div className="error-box">

            {error}

          </div>

        )}



        {/* Statistics */}

        <section className="stats-grid">


          <div className="dashboard-top-panel">


            <div className="dashboard-top-row">


              <h3>

                Child selector

              </h3>


            </div>



            <ChildSelector

              children={children}

              value={selectedChildId}

              onChange={(event) =>

                setSelectedChildId(

                  event.target.value

                )

              }

            />


          </div>



          <StatCard

            title="Total observations"

            value={recentObservations.length || 0}

            subtitle="Recorded developmental observations"

            tone="primary"

          />



          <StatCard

            title="Child profile"

            value={children.length || 0}

            subtitle="Profiles available"

            tone="success"

          />


        </section>



        {/* Summary */}

        <section className="dashboard-summary">


          <div className="summary-card">


            <h3>

              Child profile summary

            </h3>



            {children.length === 0 ? (


              <p className="muted-text">

                No child profiles yet.

              </p>


            ) : (


              children

                .filter(

                  (child) =>

                    String(child.id) ===

                    String(selectedChildId)

                )

                .map((child) => (


                  <div

                    key={child.id}

                    className="child-summary-box"

                  >


                    <h4>

                      {child.name}

                    </h4>



                    <p>

                      <strong>DOB:</strong>{' '}

                      {child.date_of_birth ||

                        'Not provided'}

                    </p>



                    <p>

                      <strong>Age:</strong>{' '}

                      {child.age ??

                        'Not provided'}

                    </p>



                    <p>

                      <strong>Gender:</strong>{' '}

                      {child.gender ||

                        'Not provided'}

                    </p>



                    <p>

                      <strong>Interests:</strong>{' '}

                      {child.interests ||

                        'Not provided'}

                    </p>


                  </div>


                ))

            )}


          </div>



          <div className="summary-card">


            <h3>

              Frequently observed developmental domains

            </h3>



            {domainSummary.length === 0 ? (


              <p className="muted-text">

                No patterns available yet.

              </p>


            ) : (


              <div className="frequency-list">


                {domainSummary.map((item) => (


                  <div

                    key={item.domain}

                    className="frequency-row"

                  >


                    <span>

                      {item.domain}

                    </span>



                    <strong>

                      {item.count}

                    </strong>


                  </div>


                ))}


              </div>


            )}


          </div>


        </section>



        {/* Charts */}

        <section className="chart-grid">


          <div className="stat-card chart-card">


            <ProgressChart

              type="area"

              data={timelineData}

              dataKey="count"

              xKey="date"

              title="Observation count over time"

            />


          </div>



          <div className="stat-card chart-card">


            <ProgressChart

              type="pie"

              data={domainChartData}

              dataKey="value"

              labelKey="name"

              title="Observations by developmental domain"

            />


          </div>


        </section>



        {/* Recent Observations */}

        <section className="dashboard-bottom-grid">


          <div className="summary-card full-width">


            <h3>

              Recent observations

            </h3>



            {recentCards.length === 0 ? (


              <p className="muted-text">

                No recent observations recorded.

              </p>


            ) : (


              <div className="recent-list">


                {recentCards.map((observation) => (


                  <ObservationCard

                    key={observation.id}

                    observation={observation}

                  />


                ))}


              </div>


            )}


          </div>



          <div className="summary-card full-width">


            <h3>

              Observation patterns

            </h3>



            {domainSummary.length === 0 ? (


              <p className="muted-text">

                No observation patterns available yet.

              </p>


            ) : (


              <div className="frequency-list">


                {domainSummary.map((item) => (


                  <div

                    key={item.domain}

                    className="frequency-row"

                  >


                    <span>

                      {item.domain}

                    </span>



                    <strong>

                      {item.count}

                    </strong>


                  </div>


                ))}


              </div>


            )}


          </div>


        </section>



        {/* Activity Trends */}

        <section className="dashboard-bottom-grid">


          <div className="summary-card full-width">


            <h3>

              Observed activity trends

            </h3>



            <ProgressChart

              type="line"

              data={timelineData}

              dataKey="count"

              xKey="date"

              title="Observed activity trends"

            />


          </div>


        </section>



        {/* Safety Notice */}

        <div className="safety-notice">


          This application is intended for developmental monitoring

          and caregiver support. It is not a diagnostic tool or a

          substitute for professional medical advice.


        </div>



      </main>


    </div>


  );

}



export default DashboardPage;